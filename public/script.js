const socket = io();
const counter = document.getElementById('counter');

socket.on('updateCount', (count) => {
    counter.innerText = count;
});

function clickMe() {
    socket.emit('click');
}
