// =========================================================
// BLOOD DONOR WEBSITE JAVASCRIPT
// =========================================================


// =========================================================
// MOBILE NUMBER VALIDATION
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    const mobileInputs = document.querySelectorAll(
        'input[type="tel"]'
    );

    mobileInputs.forEach(function (input) {

        input.addEventListener("input", function () {

            this.value = this.value.replace(/\D/g, "");

            if (this.value.length > 10) {
                this.value = this.value.substring(0, 10);
            }

        });

    });

});


// =========================================================
// GET CURRENT LOCATION
// =========================================================

function getLocation() {

    const status = document.getElementById("locationStatus");

    const latitude = document.getElementById("latitude");

    const longitude = document.getElementById("longitude");


    if (!navigator.geolocation) {

        status.textContent =
            "Geolocation is not supported by your browser.";

        return;
    }


    status.textContent =
        "Getting your location...";


    navigator.geolocation.getCurrentPosition(

        function (position) {

            const lat =
                position.coords.latitude;

            const lon =
                position.coords.longitude;


            latitude.value = lat;

            longitude.value = lon;


            status.textContent =
                "✓ Location captured successfully";


            status.classList.add("location-success");

        },

        function (error) {

            if (error.code === 1) {

                status.textContent =
                    "Location permission was denied.";

            } else if (error.code === 2) {

                status.textContent =
                    "Location information is unavailable.";

            } else if (error.code === 3) {

                status.textContent =
                    "Location request timed out.";

            } else {

                status.textContent =
                    "Unable to get your location.";

            }

        },

        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }

    );

}