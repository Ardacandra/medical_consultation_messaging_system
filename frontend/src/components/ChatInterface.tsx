import React, { useState, useEffect, useRef } from 'react';
import PatientProfileSidebar from './PatientProfileSidebar';

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
        <div className="flex w-full max-w-6xl h-[700px] bg-white rounded-lg shadow-xl overflow-hidden font-sans">
            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full relative">
                <div className="p-4 border-b bg-white z-10 shadow-sm flex justify-between items-center">
                    <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                        Nightingale Chat
                    </h2>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50">
                    {messages.map((msg, idx) => {
                        const isPatient = msg.sender_type === 'patient';
                        const isClinician = msg.sender_type === 'clinician';

                        return (
                            <div
                                key={idx}
                                className={`flex w-full ${isPatient ? 'justify-end' : 'justify-start'} animate-fade-in`}
                            >
                                <div className={`relative px-5 py-3 shadow-md text-sm max-w-[80%] leading-relaxed 
                                    ${isPatient
                                        ? 'bg-blue-600 text-white rounded-2xl rounded-br-sm'
                                        : isClinician
                                            ? 'bg-amber-50 border border-amber-200 text-amber-900 rounded-2xl rounded-bl-sm'
                                            : 'bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm'
                                    }`}
                                >
                                    {/* Tail */}
                                    <div
                                        className={`absolute bottom-0 w-3 h-3 
                                            ${isPatient
                                                ? '-right-1.5 bg-blue-600 [clip-path:polygon(0_0,0%_100%,100%_100%)]'
                                                : '-left-1.5 [clip-path:polygon(100%_0,0%_100%,100%_100%)] ' + (isClinician ? 'bg-amber-50' : 'bg-white border-l border-gray-200') // Border on tail is tricky with clip-path, simplified
                                            }`}
                                    />

                                    {/* Badge for Clinician */}
                                    {isClinician && (
                                        <div className="flex items-center gap-1.5 mb-2 pb-2 border-b border-amber-200/50">
                                            <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                                            <span className="text-xs font-bold uppercase tracking-wider text-amber-800">Verified Nurse</span>
                                        </div>
                                    )}

                                    <p className="whitespace-pre-wrap relative z-10">{msg.content}</p>

                                    <span className={`text-[10px] block mt-2 opacity-70 ${isPatient ? 'text-blue-100' : 'text-gray-400'} text-right`}>
                                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 bg-white border-t border-gray-100">
                    <div className="flex items-center gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Type a message..."
                            className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-6 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 text-gray-800 placeholder-gray-400 transition-all font-medium"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim()}
                            className="bg-blue-600 text-white rounded-full p-3 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg active:scale-95"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 translate-x-0.5" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            {/* Patient Profile Sidebar */}
            <PatientProfileSidebar />
        </div>
    );
};

export default ChatInterface;
