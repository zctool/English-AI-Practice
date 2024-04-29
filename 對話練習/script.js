// script.js
document.getElementById('ordering').addEventListener('click', function() {
    fetchConversation('ordering');
});

document.getElementById('working').addEventListener('click', function() {
    fetchConversation('working');
});

document.getElementById('airport').addEventListener('click', function() {
    fetchConversation('airport');
});

function fetchConversation(topic) {
    fetch(`http://localhost:5000/conversation/${topic}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('conversation').innerHTML = data.map(d => `<p>${d.speaker}: ${d.line}</p>`).join('');
        })
        .catch(error => console.error('Error fetching data: ', error));
}
