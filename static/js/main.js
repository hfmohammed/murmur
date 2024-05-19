document.addEventListener("DOMContentLoaded", function () {
  const signUpErrors = document.getElementById("signUpErrors");
  const signUpButton = document.getElementById("signUpButton");

  const inputs = {
    username: document.getElementById("username"),
    name: document.getElementById("name"),
    city: document.getElementById("city"),
    password: document.getElementById("password"),
    email: document.getElementById("email"),
  };

  function updateSignUpErrors(inputKey) {
    // console.log(key)

    const errors = [];
    const successes = [];
    const checking = [];

    Object.keys(inputs).forEach((key) => {
      const value = inputs[key].value.trim();

      if (value === "") {
        if (key !== "password" && key !== "email" && key !== "username") {
          errors.push(`${capitalizeFirstLetter(key)} cannot be empty.`);
        }
      } else if (
        (containsSymbol(value) || value.length > 100) &&
        key !== "password" &&
        key !== "email" &&
        key !== "username"
      ) {
        if (containsSymbol(value))
          errors.push(
            `${capitalizeFirstLetter(key)} cannot contain special characters.`
          );
        if (value.length > 100)
          errors.push(`${capitalizeFirstLetter(key)} is too long`);
      } else {
        if (key !== "email" && key !== "username" && key !== "password") {
          successes.push(`${capitalizeFirstLetter(key)} is valid.`);
        }
      }
    });

    // Check password and email
    checkPassword(inputs.password.value, errors, successes);
    checkEmail(inputs.email.value, errors, successes);
    checkUsername(inputs.username.value, errors, checking, successes);
    // Clear previous messages
    signUpErrors.innerHTML = "";

    // Display errors
    errors.forEach((error) => displayMessage(error, "red"));

    // Display successes
    successes.forEach((success) => displayMessage(success, "green"));

    // Display checking
    checking.forEach((e) => displayMessage(e, "blue"));

    // Enable or disable sign-up button based on errors
    signUpButton.disabled = errors.length > 0;
  }

  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  function containsSymbol(text) {
    return /[^a-zA-Z0-9\s]/.test(text);
  }

  function displayMessage(message, color) {
    const li = document.createElement("li");
    li.textContent = message;
    li.style.color = color;
    signUpErrors.appendChild(li);
  }

  function checkUsername(username, errors, checking, successes) {
    usernameErrors = 0;
    username = username.trim();

    if (username === "") {
      errors.push("Username is invalid");
    } else if (containsSymbol(username) || username.length > 100) {
      if (containsSymbol(username))
        errors.push("Username cannot contain special characters");
      if (username.length > 100) errors.push("Username is too long");
    } else {
      checkUsernameAvailability(username, errors, checking)
        .then((result) => {
          // Use the result here
          if (result) {
            successes.push("Username is available");
          }
          successes.forEach((success) => displayMessage(success, "green"));
        })
        .catch((error) => {
          // Handle any errors here
          console.error("Error:", error);
        });
    }
  }

  function checkPassword(password, errors, successes) {
    passwordErrors = 0;
    if (password.length < 8) {
      errors.push("Password must be at least 8 characters long.");
      passwordErrors += 1;
    }
    if (password.length > 100) {
      errors.push("Password is too long.");
      passwordErrors += 1;
    }
    if (!/[A-Z]/.test(password)) {
      errors.push("Password must contain at least one uppercase letter.");
      passwordErrors += 1;
    }
    if (!/[a-z]/.test(password)) {
      errors.push("Password must contain at least one lowercase letter.");
      passwordErrors += 1;
    }
    if (!/\d/.test(password)) {
      errors.push("Password must contain at least one number.");
      passwordErrors += 1;
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push("Password must contain at least one special character.");
      passwordErrors += 1;
    }
    if (passwordErrors === 0) {
      successes.push("Password is Valid");
    }
  }

  function checkUsernameAvailability(username, errors, checking) {
    checking.push("Checking username...");
    displayMessage("Checking username...", "blue"); // Display the message immediately

    return new Promise((resolve, reject) => {
      fetch(`/check_username?username=${username}`)
        .then((response) => response.json())
        .then((data) => {
          let result = 0;
          if (!data.available) {
            errors.push("Username is not available");
          } else {
            result = 1;
          }
          // Remove the "Checking username..." message after the fetch operation completes
          const index = checking.indexOf("Checking username...");
          if (index !== -1) {
            checking.splice(index, 1);
          }
          // Update display after message is removed
          signUpErrors.innerHTML = "";
          errors.forEach((error) => displayMessage(error, "red"));
          // Display successes if any

          resolve(result); // Resolve the Promise with the result
        })
        .catch((error) => {
          errors.push("Error checking username availability.");
          // Remove the "Checking username..." message in case of error
          const index = checking.indexOf("Checking username...");
          if (index !== -1) {
            checking.splice(index, 1);
          }
          // Update display after message is removed
          signUpErrors.innerHTML = "";
          errors.forEach((error) => displayMessage(error, "red"));
          // Display successes if any

          reject(error); // Reject the Promise with the error
        });
    });
  }
  function checkEmail(email, errors, successes) {
    if (email.length > 100) {
      errors.push("Email is too long.");
      passwordErrors += 1;
    }
    if (!validateEmail(email)) {
      errors.push("Invalid email address.");
    } else {
      successes.push("Valid email address.");
    }
  }

  // Add event listeners to all input fields
  Object.keys(inputs).forEach((key) => {
    inputs[key].addEventListener("input", () => updateSignUpErrors(key));
  });

  // Call the updateSignUpErrors function initially
  updateSignUpErrors();
});

function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}
