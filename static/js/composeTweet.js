document.addEventListener("DOMContentLoaded", function() {
    const tweetTextarea = document.getElementById("tweet");
    const tweetButton = document.getElementById("tweet-button");
    const charCount = document.getElementById("char-count");
    const errorMessage = document.getElementById("error-message");

    tweetTextarea.addEventListener("input", function() {
        const tweetLength = tweetTextarea.value.length;
        charCount.textContent = `${tweetLength}/500`;

        if (tweetLength > 500) {
            errorMessage.style.display = "block";
            tweetButton.disabled = true
        } else {
            errorMessage.style.display = "none";
            tweetButton.disabled = false
        }
    });
});
