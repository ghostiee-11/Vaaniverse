document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const recordBtn = document.getElementById('record-btn');
    const ttsAudio = document.getElementById('tts-audio');

    const FASTAPI_URL = 'http://localhost:8000';
    let mediaRecorder;
    let audioChunks = [];

    // --- Event Listeners ---
    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
    recordBtn.addEventListener('click', handleVoiceRecording);

    // --- Core Functions ---

    function handleSendMessage() {
        const query = chatInput.value;
        if (!query.trim()) return;

        addMessageToUI(query, 'user');
        chatInput.value = '';
        getAIResponse(query);
    }

    async function getAIResponse(query) {
        const thinkingBubble = addMessageToUI('Vaani is thinking...', 'thinking');
        
        try {
            const response = await fetch(`${FASTAPI_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, sid: 'webapp-session' })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            
            // Remove the "thinking..." bubble
            thinkingBubble.remove();
            
            // Add the final AI message
            addMessageToUI(data.response_text, 'assistant');
            
            // Play the AI's voice
            if (data.audio_url) {
                playAudio(data.audio_url);
            }

        } catch (error) {
            thinkingBubble.remove();
            addMessageToUI('Sorry, something went wrong. Please check the backend server and try again.', 'assistant');
            console.error('Error fetching AI response:', error);
        }
    }

    async function handleVoiceRecording() {
        if (!mediaRecorder || mediaRecorder.state === "inactive") {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    audioChunks = []; // Reset chunks
                    await transcribeAudio(audioBlob);
                };
                
                mediaRecorder.start();
                recordBtn.classList.add('recording');
                recordBtn.innerText = '⏹️';
            } catch (error) {
                console.error('Error accessing microphone:', error);
                alert('Microphone access denied. Please allow microphone access in your browser settings.');
            }
        } else {
            mediaRecorder.stop();
            recordBtn.classList.remove('recording');
            recordBtn.innerText = '🎤';
        }
    }

    async function transcribeAudio(audioBlob) {
        const thinkingBubble = addMessageToUI('Transcribing audio...', 'thinking');
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recorded_audio.wav');

        try {
            const response = await fetch(`${FASTAPI_URL}/transcribe-webaudio`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            thinkingBubble.remove();
            
            if (data.transcription) {
                addMessageToUI(`(Heard: "${data.transcription}")`, 'user');
                getAIResponse(data.transcription);
            } else {
                addMessageToUI('Sorry, I could not understand the audio.', 'assistant');
            }
        } catch (error) {
            thinkingBubble.remove();
            addMessageToUI('Sorry, there was an error with transcription.', 'assistant');
            console.error('Error transcribing audio:', error);
        }
    }

    function addMessageToUI(text, role) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message', role);

        const messageParagraph = document.createElement('p');
        messageParagraph.innerText = text;
        
        messageWrapper.appendChild(messageParagraph);
        chatWindow.appendChild(messageWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the latest message
        return messageWrapper;
    }

    function playAudio(url) {
        ttsAudio.src = url;
        ttsAudio.play().catch(e => console.error("Audio playback failed:", e));
    }
});