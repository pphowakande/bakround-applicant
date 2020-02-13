function showTour(tour, tour_type) {
    var mark_done = function (){
        $.ajax({
            url: '/employer/dismiss_tour/' + tour_type,
            method: "POST",
            headers: {
                "X-CSRFToken": window.csrf_token
            }
        });
    };

    tour.oncomplete(mark_done)
        .onexit(mark_done)
        .start();
}

function startJobsTour() {
    var tour = introJs().setOption("skipLabel", "Dismiss")
        .addStep({
            intro: "This is the jobs page!  This page shows you all the jobs that your organization has registered in the system.",
            position: 'center'
        }).addStep({
            element: $('#add_a_new_job')[0],
            intro: "You can add new jobs by clicking here.",
            position: 'bottom-right-aligned'
        }).addStep({
            element: $('#open_or_all_jobs_panel')[0],
            intro: 'Jobs can be marked as open or closed.  By default, only the open jobs that you follow are shown on this page.  Click "Open Jobs" to see all of your organization\'s open jobs.  Click "All Jobs" to see all of your organization\'s jobs, both open and closed.',
            position: 'bottom-right-aligned'
        });

    var manage_custom_jobs = $('#manage_custom_jobs');
    if (manage_custom_jobs.length){
        tour.addStep({
            element: manage_custom_jobs[0],
            intro: "You can customize our standard job profiles to better fit your needs.",
            position: 'bottom-right-aligned'
        });
    }

    tour.addStep({
            element: $('#show_tour')[0],
            intro: "You can click this button to see this tour again.",
            position: 'bottom-right-aligned'
        });

    showTour(tour, "jobs");
    return tour;
}

    function show_my_open_jobs()
    {
      style_selected("#show_my_open_jobs");
      $(".closed-job").addClass('hidden');
      $(".not-my-job").addClass('hidden');
      adjust_locations();
    }

    function show_open_jobs()
    {
      style_selected("#show_open_jobs");
      $(".not-my-job").removeClass('hidden');
      $(".closed-job").addClass('hidden');
      adjust_locations();
    }

    function show_all_jobs()
    {
      style_selected("#show_all_jobs");
      $(".closed-job").removeClass('hidden');
      $(".not-my-job").removeClass('hidden');
      adjust_locations();
    }

    function style_selected(selected)
    {
      $(".job_filter").css('font-weight', '300');
      $(selected).css('font-weight', 'bold');
    }

    function adjust_locations()
    {
      // First, hide every location.
      $("div.location").addClass("hidden");

      // Now, for every job that has not been set to hidden, make that job's location visible.
      $("div.card-top").not(".hidden").closest("div.location").removeClass("hidden");
    }

    function ask_about_deleting_job(job_id)
    {
        $("#deletion_dialog").dialog({
          dialogClass: "no-close",
          closeOnEscape: false,
          resizable: false,
          height: "auto",
          width: 700,
          modal: true,
          buttons: {
            "Yes": function (){delete_job(job_id)},
            "No": close_deletion_dialog
          }
        });
    }

    function close_deletion_dialog()
    {
        $("#deletion_dialog").dialog("close");
    }

    function delete_job(job_id)
    {
        close_deletion_dialog();
        $("#job_card_" + job_id).addClass('deleted-job');
        $.ajax({
            url: "/employer/delete_job/" + job_id,
            method: "POST",
            headers: {
                'X-CSRFToken': window.csrf_token
            },
        });
    }
