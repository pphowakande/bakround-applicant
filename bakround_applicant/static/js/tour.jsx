import introJs from 'intro.js';
import Networking from './networking';
import 'intro.js/introjs.css';

// // Example steps
// let steps = [
//     {
//         element: () => null,
//         intro: "",
//         position: "bottom-{left,right}-aligned"
//     }
// ];

function isElement(element) {
    return element instanceof Element || element instanceof HTMLDocument;  
}

export function runTour(steps, tourKey=null) {
    let markDone = () => tourKey ? Networking.json("POST", `/employer/dismiss_tour/${tourKey}`) : null;
    let tour = introJs().setOption("skipLabel", "Dismiss");

    let addedStep = false;

    for (var i = 0; i < steps.length; i++) {
        let step = steps[i];
        if (step.hasOwnProperty('element')) {
            let el = null;
            if (typeof step.element === 'function') el = step.element();
            else if (isElement(step.element))       el = step.element;
            else if (step.element)                  el = document.querySelector(step.element);
            if (el) {
                step.element = el;
                tour = tour.addStep(step);
                addedStep = true;
            }
        } else {
            tour = tour.addStep(step);
            addedStep = true;
        }

    }

    if (addedStep) tour.oncomplete(markDone).onexit(markDone).start();
};

