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
            <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-50">
                {messages.map((msg, idx) => {
                    const isPatient = msg.sender_type === 'patient';
                    const isClinician = msg.sender_type === 'clinician';

                    return (
                        <div
                            key={idx}
                            className={`flex w-full ${isPatient ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                        >
                            <div className={`flex max-w-[80%] ${isPatient ? 'flex-row-reverse' : 'flex-row'} items-end gap-2`}>
                                {/* Avatar/Icon placeholder could go here */}

                                <div
                                    className={`relative px-4 py-3 shadow-sm text-sm 
                                        ${isPatient
                                            ? 'bg-blue-600 text-white rounded-2xl rounded-br-sm'
                                            : isClinician
                                                ? 'bg-amber-50 border border-amber-200 text-amber-900 rounded-2xl rounded-bl-sm'
                                                : 'bg-gray-200 text-gray-900 rounded-2xl rounded-bl-sm border border-gray-300'
                                        }`}
                                >
                                    {/* Tail for Patient */}
                                    {isPatient && (
                                        <div className="absolute bottom-[0px] -right-[6px] w-0 h-0 
                                            border-l-[12px] border-l-blue-600 outline-none
                                            border-b-[12px] border-b-transparent 
                                            transform -rotate-12 filter drop-shadow-sm pointer-events-none">
                                        </div>
                                    )}

                                    {/* Tail for Others */}
                                    {!isPatient && (
                                        <div className={`absolute bottom-[0px] -left-[6px] w-0 h-0 
                                            border-r-[12px] outline-none
                                            border-b-[12px] border-b-transparent 
                                            transform rotate-12 filter drop-shadow-sm pointer-events-none
                                            ${isClinician ? 'border-r-amber-50' : 'border-r-gray-200'}`}>
                                        </div>
                                    )}

                                    {isClinician && (
                                        <div className="flex items-center gap-1 mb-1 text-amber-700/80">
                                            <span className="text-[10px] font-bold uppercase tracking-wider">Verified Nurse</span>
                                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                        </div>
                                    )}

                                    <div className="leading-relaxed">
                                        {msg.content}
                                    </div>

                                    <div className={`text-[10px] mt-1 text-right  ${isPatient ? 'text-blue-100' : 'text-gray-400'}`}>
                                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
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
                    className="flex-1 p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
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
