var introJs = require('../vendor/introjs-2.4.0/intro.min.js').introJs

var startTour = function(updateTourSettingCallback) {
    var tour = introJs().setOption("skipLabel", "Dismiss")
        .addStep({
            intro: "Welcome to Bakround! Let's get started...",
            position: 'center'
        }).addStep({
            element: $('a#btnUploadResume')[0],
            intro: "To get started quickly, you can upload your resume.   Your resume will be analyzed, and its data will be used to fill out your profile.",
            position: 'bottom-right-aligned'
        }).addStep({
            element: $('div.scoreContainer')[0],
            intro: "Your bScore is an indicator of how recruiters view you in the marketplace. You'll need to make some updates to your profile in order to receive a more complete score. <br /><br /> And don't worry if you don't see anything here yet. We'll calculate it for you once you fill out your profile and click 'Regenerate Score'.",
            position: 'bottom-left-aligned'
        }).addStep({
            element: $('div.section-content')[0],
            intro: "Update your skills, education, experience, and certifications here.",
            position: 'top'
        }).addStep({
            element: $('a#btnRescore')[0],
            intro: "Remember to regenerate your score once you're done making your updates.",
            position: 'bottom-right-aligned'
        }).addStep({
            element: $('div.progress')[0],
            intro: "Your bScore is calculated using the data in your profile. Make sure you maximize your score by providing as much information as possible.",
            position: 'bottom-right-aligned'
        }).addStep({
            element: $('div#chart_div')[0],
            intro: "You can get analysis into where you stand compared to your peers, and also track your score over time.",
            position: 'bottom-right-aligned'
        }).addStep({
            element: $('a#btnShareProfile')[0],
            intro: "Share your profile with employers by sending them a link to view your profile.",
            position: 'bottom-right-aligned'
        });

    if ($("#btnClaimProfile").length){
        tour = tour.addStep({
            element: $('a#btnClaimProfile')[0],
            intro: "We also have a pre-filled profile for you in our records.  You can click the link to claim this profile.",
            position: 'bottom-right-aligned'
        });
    }

    tour = tour.addStep({
        element: $('a#btnSeeTourAgain')[0],
        intro: "You can click this link to see this tour again.",
        position: 'bottom-right-aligned'
    });

    tour.oncomplete(updateTourSettingCallback)
        .onexit(updateTourSettingCallback)
        .start();
};

module.exports = startTour;
