// TASKIFY JAVASCRIPT


// DARK MODE
function toggleDarkMode() {

    document.body.classList.toggle("dark-mode");

    const isDark = document.body.classList.contains("dark-mode");

    localStorage.setItem("taskifyDarkMode", isDark);

}


// LOAD SAVED THEME
document.addEventListener("DOMContentLoaded", function () {

    const savedTheme = localStorage.getItem("taskifyDarkMode");

    if (savedTheme === "true") {
        document.body.classList.add("dark-mode");
    }

});


// TASK FORM VALIDATION
document.addEventListener("DOMContentLoaded", function () {

    const taskForm = document.querySelector(".task-form");

    if (taskForm) {

        taskForm.addEventListener("submit", function (event) {

            const taskInput = taskForm.querySelector(
                'input[name="title"]'
            );

            if (!taskInput.value.trim()) {

                event.preventDefault();

                alert("Please enter a task!");

            }

        });

    }

});


// CONFIRM LOGOUT
document.addEventListener("DOMContentLoaded", function () {

    const logoutButton = document.querySelector(".logout");

    if (logoutButton) {

        logoutButton.addEventListener("click", function (event) {

            const confirmLogout = confirm(
                "Are you sure you want to logout?"
            );

            if (!confirmLogout) {
                event.preventDefault();
            }

        });

    }

});