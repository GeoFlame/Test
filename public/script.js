const socket = io();
const counterDisplay = document.getElementById('counter');

// Receive the initial count from the server
socket.on('updateCount', (count) => {
    counterDisplay.textContent = count;
});

// Send click event to server
function clickMe() {
    socket.emit('click');
}

// Animate the counter update for effect
socket.on('updateCount', (count) => {
    counterDisplay.style.transform = "scale(1.1)"; // Slightly enlarge on update
    counterDisplay.textContent = count;

    // Reset to original scale after animation
    setTimeout(() => {
        counterDisplay.style.transform = "scale(1)";
    }, 100);
});
