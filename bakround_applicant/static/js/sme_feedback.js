
  var OverrideValidate = false;

  function is_interview_question_unanswered(){
    return !$("#should_interview_yes").is(':checked') && !$("#should_interview_no").is(':checked');
  }

  function is_comment_empty(){
    return $("#comment").val() == "";
  }

  function is_comment_too_short(){
    return $("#comment").val().length < 30;
  }

  function is_faulty_resume_unanswered(){
    return !$("#column_wrong_job").is(':checked') && !$("#column_wrong_language").is(':checked') && !$("#column_incomplete").is(':checked');
  }

  function validate_form(){
    if (OverrideValidate){
      return true;
    }

    var score = document.getElementById("bscore_value").value;
    if (score == ""){
      // an empty score is OK
    } else if (score >= 300 && score <= 850 && score == Math.floor(score)){
      // the score is OK
    } else {
      alert("The score must be a whole number in the range 300-850.");
      return false;
    }



    if (score == "" && (is_interview_question_unanswered() || is_comment_empty() || is_faulty_resume_unanswered())){
      alert("Please tell us more about why you did not score this resume.  Answer the interview question, provide a comment, and select one of the first three checkboxes.");
      return false;
    }



    if (is_comment_too_short()){
      alert("Please provide a longer comment.  Your comment must be at least 30 characters long.");
      return false;
    }



    if (is_interview_question_unanswered()){
      alert("Please answer the question about interviewing this applicant.");
      return false;
    }



    if (ask_about_low_scores && score && score < 400){
      show_dialog();
      return false;
    }



    return true;
  }

  function track_resume_open() {
    $.ajax({
         headers: {
                    'X-CSRFToken': csrf_token
                },
         type: "POST",
         contentType: 'application/json; charset=utf-8',
         url: "/sme_feedback/open_resume",
         data: JSON.stringify({ 'sme_id': sme_id, 'profile_resume_id': resume_id })
    });
    return false;
  }

  function set_score_from_click(event, elt){
    var x = event.offsetX, y = event.offsetY;
    var raw_score = 300 + (x - 15);

    // var rounded_score = Math.round(raw_score / 10) * 10;
    var rounded_score = raw_score;
    if (rounded_score < 300){
      rounded_score = 300;
    } else if (rounded_score > 850){
      rounded_score = 850;
    }

    $("#bscore_value").val(rounded_score);

    var marker = $("#slider_marker");
    var markerX = $(elt).offset().left + (rounded_score - 300) + 10;
    var markerY = $(elt).offset().top + 12;
    marker.css({left: markerX + 'px', top: markerY + 'px'});
    marker.show();
  }

  function submit_from_dialog(){
    $("#low_score_dialog").dialog("close");
    OverrideValidate = true;

    if (do_not_ask_again()){
      submit_do_not_ask_again().then(function (){
        $("#main_form").submit();
      });
    } else {
      $("#main_form").submit();
    }
  }

  function close_dialog(){
    $("#low_score_dialog").dialog("close");

    if (do_not_ask_again()){
      submit_do_not_ask_again();
    }
  }

  function show_dialog(){
    $( "#low_score_dialog" ).dialog({
      dialogClass: "no-close",
      closeOnEscape: false,
      resizable: false,
      height: "auto",
      width: 400,
      modal: true,
      buttons: {
        "Yes": submit_from_dialog,
        "No": close_dialog
      }
    });

    var do_not_ask_again_div = $("#do_not_ask_again_div");
    $("div.ui-dialog-buttonpane").append(do_not_ask_again_div);
    do_not_ask_again_div.show();
  }

  function do_not_ask_again(){
    return $("#do_not_ask_again").is(":checked");
  }

  function submit_do_not_ask_again(){
    ask_about_low_scores = false;
    return $.ajax({
      url: do_not_ask_again_url,
      method: "POST",
      headers: {
        'X-CSRFToken': csrf_token
      },
      data: {
        guid: sme_guid
      }
    });
  }



  // Functions for contact dialog (contact candidate directly from SME feedback page)

  function show_contact_dialog(){
    $("#contact_dialog").dialog({
      dialogClass: "no-close",
      closeOnEscape: false,
      resizable: false,
      height: "auto",
      width: 700,
      modal: true,
      buttons: {
        "Contact": submit_from_contact_dialog,
        "Cancel": close_contact_dialog
      }
    });
  }

  function close_contact_dialog(){
    $("#contact_dialog").dialog("close");
  }

  function submit_from_contact_dialog(){
    var employer_job_id = $("#id_employer_job").val();
    if (!employer_job_id){
        alert("Please select a job.");
        return;
    }

    $("#contact_dialog").dialog("close");

    return $.ajax({
      url: contact_endpoint,
      method: "POST",
      headers: {
        'X-CSRFToken': csrf_token
      },
      data: {
        sme_guid: sme_guid,
        resume_id: resume_id,
        employer_job_id: employer_job_id
      }
    });
  }

  function refresh_job_dropdown(){
    $.ajax({
      url: job_dropdown_endpoint,
      method: "POST",
      headers: {
        'X-CSRFToken': csrf_token
      },
      data: {
        sme_guid: sme_guid
      },
      success: function (response){
        $("#id_employer_job").replaceWith(response);
        $("#current_message").html("");
        add_handler_to_dropdown();
        $("#edit_link").attr("href", "#");
      }
    });
  }

  function show_message_for_selected_job(){
    var selected_job = $("#id_employer_job").val();
    var edit_href = selected_job ? ("/employer/job_settings/" + selected_job + "#custom_email_body") : "#";

    $.ajax({
      url: job_message_endpoint,
      method: "POST",
      headers: {
        'X-CSRFToken': csrf_token
      },
      data: {
        sme_guid: sme_guid,
        employer_job_id: selected_job
      },
      success: function (response){
        $("#current_message").html(response);
        $("#edit_link").attr("href", edit_href);
      }
    });
  }

  function add_handler_to_dropdown(){
    $("#id_employer_job").on('change', function (){
      show_message_for_selected_job();
    });
  }
