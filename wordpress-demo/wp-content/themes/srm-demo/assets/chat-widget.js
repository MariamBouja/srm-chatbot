/**
 * Floating chatbot widget: toggles a slide-out iframe panel pointing at the
 * Streamlit chatbot app. The iframe's real src is set on first open (lazy
 * load) so the Streamlit app doesn't load on every WordPress page view.
 */
(function () {
    'use strict';

    function init() {
        var toggle = document.getElementById('srm-chat-toggle');
        var panel = document.getElementById('srm-chat-panel');
        var closeBtn = document.getElementById('srm-chat-panel-close');
        var iframe = document.getElementById('srm-chat-iframe');

        if (!toggle || !panel || !iframe) {
            return;
        }

        function isOpen() {
            return !panel.hidden;
        }

        function open() {
            if (!iframe.src || iframe.src === 'about:blank') {
                iframe.src = iframe.dataset.src;
            }
            panel.hidden = false;
            toggle.classList.add('is-open');
            toggle.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-label', "Fermer l'assistant SRM-SM");
        }

        function close() {
            panel.hidden = true;
            toggle.classList.remove('is-open');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', "Ouvrir l'assistant SRM-SM");
        }

        function toggleOpen() {
            if (isOpen()) {
                close();
            } else {
                open();
            }
        }

        toggle.addEventListener('click', toggleOpen);
        closeBtn.addEventListener('click', close);

        // Any element with .js-open-chatbot (e.g. the homepage "Demander à
        // l'assistant" button) opens the widget directly.
        document.querySelectorAll('.js-open-chatbot').forEach(function (el) {
            el.addEventListener('click', function () {
                if (!isOpen()) {
                    open();
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
