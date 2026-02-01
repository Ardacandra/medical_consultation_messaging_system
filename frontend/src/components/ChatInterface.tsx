import React, { useState, useEffect, useRef } from 'react';

// Types
interface Message {
    id: number;
    sender_type: 'patient' | 'ai' | 'clinician';
    content: string;
    timestamp: string;
}

const ChatInterface: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [conversationId, setConversationId] = useState<number>(0);
    const messagesEndRef = useRef<null | HTMLDivElement>(null);

    // Poll for new messages every 3 seconds
    useEffect(() => {
        if (conversationId === 0) return;

        const fetchMessages = async () => {
            try {
                const res = await fetch(`/api/v1/chat/${conversationId}/history`);
                if (res.ok) {
                    const data = await res.json();
                    // Simple state update - in prod use better diffing
                    setMessages(data);
                }
            } catch (e) { console.error(e); }
        };

        fetchMessages();
        const interval = setInterval(fetchMessages, 3000);
        return () => clearInterval(interval);
    }, [conversationId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim()) return;

        try {
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    content: input
                })
            });

            const data = await response.json();

            // If new conversation created
            if (conversationId === 0 && data.conversation_id) {
                setConversationId(data.conversation_id);
            }

            // If escalation
            if (data.message && data.escalation_id) {
                // Add system message
                const sysMsg: Message = {
                    id: Date.now(),
                    sender_type: 'ai',
                    content: `[SYSTEM] ${data.message}`,
                    timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, {
                    id: Date.now() - 1,
                    sender_type: 'patient',
                    content: input,
                    timestamp: new Date().toISOString()
                }, sysMsg]);
            } else {
                // Normal chat reply
                setMessages(prev => [...prev, {
                    id: Date.now() - 1,
                    sender_type: 'patient',
                    content: input,
                    timestamp: new Date().toISOString()
                }, {
                    id: data.id,
                    sender_type: data.sender_type,
                    content: data.content,
                    timestamp: data.timestamp
                }]);
            }

            setInput('');
        } catch (e) {
            console.error("Error sending message", e);
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-md border rounded-lg shadow-lg bg-white">
            {/* Header */}
            <div className="p-4 border-b bg-blue-50">
                <h2 className="text-lg font-semibold text-blue-900">Nightingale Chat</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.sender_type === 'patient' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.sender_type === 'patient'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : msg.sender_type === 'clinician'
                                        ? 'bg-yellow-50 border-2 border-yellow-400 text-gray-800 rounded-bl-none shadow-sm'
                                        : 'bg-gray-100 text-gray-800 rounded-bl-none'
                                }`}
                        >
                            {msg.sender_type === 'clinician' && (
                                <div className="text-xs font-bold text-yellow-700 mb-1 uppercase tracking-wider">
                                    Verified Nurse
                                </div>
                            )}
                            {msg.content}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t bg-gray-50 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Type your health concern..."
                    className="flex-1 p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                    onClick={sendMessage}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;
