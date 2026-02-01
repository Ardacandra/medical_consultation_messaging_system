import React, { useState, useEffect } from 'react';

interface Medication { value: string; }
interface Symptom { value: string; }
interface Snapshot {
    medications?: Medication[];
    symptoms?: Symptom[];
}

interface Escalation {
    id: number;
    conversation_id: number;
    trigger_message_id: number;
    status: string;
    triage_summary: string;
    patient_profile_snapshot?: Snapshot;
}

interface ClinicianDashboardProps {
    token: string;
}

const ClinicianDashboard: React.FC<ClinicianDashboardProps> = ({ token }) => {
    const [escalations, setEscalations] = useState<Escalation[]>([]);
    const [replyingTo, setReplyingTo] = useState<number | null>(null);
    const [replyContent, setReplyContent] = useState('');

    const fetchEscalations = React.useCallback(async () => {
        try {
            const res = await fetch('/api/v1/escalations/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setEscalations(data);
            }
        } catch (e) {
            console.error("Failed to fetch escalations", e);
        }
    }, []);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        fetchEscalations();
        const interval = setInterval(fetchEscalations, 5000);
        return () => clearInterval(interval);
    }, [fetchEscalations, token]);

    const sendReply = async (id: number) => {
        if (!replyContent) return;

        try {
            const res = await fetch(`/api/v1/escalations/${id}/reply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: replyContent })
            });

            if (res.ok) {
                // Remove from list or refresh
                setReplyingTo(null);
                setReplyContent('');
                fetchEscalations();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const renderSnapshot = (snapshot: Snapshot | undefined) => {
        if (!snapshot || !snapshot.medications) return <span className="text-gray-400 italic">No snapshot</span>;
        const meds = snapshot.medications.map((m) => m.value).join(", ");
        const symptoms = snapshot.symptoms ? snapshot.symptoms.map((s) => s.value).join(", ") : "";
        return (
            <div className="text-xs text-gray-500 mt-1">
                <p><strong>Meds:</strong> {meds || 'None'}</p>
                <p><strong>Symp:</strong> {symptoms || 'None'}</p>
            </div>
        );
    };

    return (
        <div className="w-full max-w-6xl p-6 bg-white shadow-md rounded-lg">
            <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b pb-2">Clinician Dashboard</h2>

            <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                    <thead>
                        <tr className="bg-gray-100 text-gray-600 uppercase text-sm leading-normal">
                            <th className="py-3 px-6 text-left">ID</th>
                            <th className="py-3 px-6 text-left">Reason & Snapshot</th>
                            <th className="py-3 px-6 text-left">Status</th>
                            <th className="py-3 px-6 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-600 text-sm font-light">
                        {escalations.length === 0 ? (
                            <tr><td colSpan={4} className="py-4 text-center">No pending escalations.</td></tr>
                        ) : escalations.map(esc => (
                            <tr key={esc.id} className="border-b border-gray-200 hover:bg-gray-50">
                                <td className="py-3 px-6 text-left whitespace-nowrap font-medium">{esc.id}</td>
                                <td className="py-3 px-6 text-left">
                                    <div className="text-red-600 font-semibold">{esc.triage_summary}</div>
                                    {renderSnapshot(esc.patient_profile_snapshot)}
                                </td>
                                <td className="py-3 px-6 text-left">
                                    <span className={`py-1 px-3 rounded-full text-xs ${esc.status === 'resolved' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'}`}>
                                        {esc.status}
                                    </span>
                                </td>
                                <td className="py-3 px-6 text-center">
                                    {replyingTo === esc.id ? (
                                        <div className="flex flex-col gap-2">
                                            <input
                                                className="border p-1 rounded"
                                                value={replyContent}
                                                onChange={e => setReplyContent(e.target.value)}
                                                placeholder="Type reply..."
                                            />
                                            <div className="flex gap-2 justify-center">
                                                <button
                                                    onClick={() => sendReply(esc.id)}
                                                    className="bg-green-500 text-white px-3 py-1 rounded text-xs"
                                                >
                                                    Send
                                                </button>
                                                <button
                                                    onClick={() => setReplyingTo(null)}
                                                    className="bg-gray-400 text-white px-3 py-1 rounded text-xs"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => setReplyingTo(esc.id)}
                                            disabled={esc.status === 'resolved'}
                                            className={`py-1 px-3 rounded text-xs ${esc.status === 'resolved' ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'}`}
                                        >
                                            Reply
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ClinicianDashboard;
