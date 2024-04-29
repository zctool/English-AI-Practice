// script.js
document.getElementById('signin-btn').addEventListener('click', function() {
    fetch('/113-NTUB', {
        method: 'POST'
    }).then(response => response.json())
    .then(data => {
        document.getElementById('message').innerText = data.message;
    }).catch(error => console.error('Error:', error));
});
