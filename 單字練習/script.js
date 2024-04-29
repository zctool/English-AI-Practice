function searchWord() {
    var input = document.getElementById('searchInput').value;
    fetch(`http://localhost:5000/vocabulary?keyword=${input}`)
        .then(response => response.json())
        .then(data => {
            var resultDiv = document.getElementById('wordResult');
            resultDiv.innerHTML = '';
            if (data.length > 0) {
                data.forEach(word => {
                    var p = document.createElement('p');
                    p.textContent = `Word: ${word.word}, Definition: ${word.definition}, Example: ${word.example_sentence}`;
                    resultDiv.appendChild(p);
                });
            } else {
                resultDiv.textContent = 'No results found.';
            }
        })
        .catch(error => console.error('Error fetching vocabulary:', error));
}
