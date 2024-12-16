document.getElementById('send-button').addEventListener('click', function() {
    let userMessage = document.getElementById('message-input').value;
    if (userMessage.trim() !== "") {
        appendMessage("Вы: " + userMessage);
        document.getElementById('message-input').value = "";

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            appendMessage("Бот: " + data.response);
        });
    }
});

function appendMessage(message) {
    let chatBox = document.getElementById('chat-box');
    let messageElement = document.createElement('p');
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}
