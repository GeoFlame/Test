// server.js
const express = require('express');
const http = require('http');
const { MongoClient } = require('mongodb');
const socketIo = require('socket.io');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const mongoUrl = process.env.MONGO_URL;
let clickCollection;

MongoClient.connect(mongoUrl, { useUnifiedTopology: true })
    .then(client => {
        console.log("Connected to MongoDB");
        const db = client.db('clickCounterDB');
        clickCollection = db.collection('clicks');
        clickCollection.updateOne(
            { _id: "globalClicks" },
            { $setOnInsert: { count: 0 } },
            { upsert: true }
        );
    })
    .catch(error => console.error("MongoDB connection error:", error));

app.use(express.static('public'));

io.on('connection', (socket) => {
    clickCollection.findOne({ _id: "globalClicks" })
        .then(result => socket.emit('updateCount', result.count));
    
    socket.on('click', () => {
        clickCollection.findOneAndUpdate(
            { _id: "globalClicks" },
            { $inc: { count: 1 } },
            { returnDocument: "after" }
        ).then(result => io.emit('updateCount', result.value.count));
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
