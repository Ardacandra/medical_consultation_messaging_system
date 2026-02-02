import React, { useState, useEffect } from 'react';

// Types
interface PatientListItem {
    id: number;
    email: string;
    last_active: string | null;
    unread_count: number;
    risk_status: 'normal' | 'escalated';
}

interface Medication { value: string; }
interface Symptom { value: string; }
interface PatientProfile {
    medications: Medication[];
    symptoms: Symptom[];
    allergies: any[];
    chief_complaint: any[];
    last_updated: string;
}

interface ClinicianDashboardProps {
    token: string;
}

const ClinicianDashboard: React.FC<ClinicianDashboardProps> = ({ token }) => {
    const [patients, setPatients] = useState<PatientListItem[]>([]);
    const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
    const [selectedProfile, setSelectedProfile] = useState<PatientProfile | null>(null);
    const [loading, setLoading] = useState(false);

    // Fetch Patient List
    const fetchPatients = async () => {
        try {
            const res = await fetch('/api/v1/clinician/patients', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPatients(data);
            }
        } catch (e) {
            console.error("Failed to fetch patients", e);
        }
    };

    // Poll for list updates
    useEffect(() => {
        fetchPatients();
        const interval = setInterval(fetchPatients, 5000);
        return () => clearInterval(interval);
    }, [token]);

    // Fetch Profile when selected
    useEffect(() => {
        if (!selectedPatientId) {
            setSelectedProfile(null);
            return;
        }

        const fetchProfile = async () => {
            setLoading(true);
            try {
                const res = await fetch(`/api/v1/clinician/patient/${selectedPatientId}/profile`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setSelectedProfile(data);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
        // Set up separate poll for profile updates if needed, or just refresh on select
        const interval = setInterval(fetchProfile, 3000);
        return () => clearInterval(interval);

    }, [selectedPatientId, token]);


    return (
        <div className="w-full w-full h-[800px] flex bg-white shadow-xl rounded-xl overflow-hidden font-sans border border-gray-100">
            {/* Left Sidebar: Patient List */}
            <div className="w-1/3 bg-gray-50 border-r border-gray-200 flex flex-col">
                <div className="p-5 border-b border-gray-200 bg-white">
                    <h2 className="text-xl font-bold text-gray-800">Patients</h2>
                    <p className="text-xs text-gray-500 mt-1">Sorted by recent activity</p>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {patients.map(patient => (
                        <div
                            key={patient.id}
                            onClick={() => setSelectedPatientId(patient.id)}
                            className={`p-4 border-b border-gray-100 cursor-pointer transition-all hover:bg-blue-50 
                                ${selectedPatientId === patient.id ? 'bg-blue-50 border-l-4 border-blue-600 shadow-inner' : 'border-l-4 border-transparent'}
                            `}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className={`font-semibold text-sm ${selectedPatientId === patient.id ? 'text-blue-900' : 'text-gray-700'}`}>
                                    {patient.email}
                                </span>
                                {patient.risk_status === 'escalated' && (
                                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-sm" title="Escalated / High Risk"></span>
                                )}
                            </div>
                            <div className="text-xs text-gray-400 font-medium">
                                {patient.last_active
                                    ? new Date(patient.last_active).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                                    : 'No activity'}
                            </div>
                        </div>
                    ))}
                    {patients.length === 0 && (
                        <div className="p-8 text-center text-gray-400 italic text-sm">No patients found.</div>
                    )}
                </div>
            </div>

            {/* Right Main Area: Patient Details */}
            <div className="flex-1 bg-white flex flex-col">
                {selectedPatientId ? (
                    <>
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                            <div>
                                <h2 className="text-2xl font-bold text-gray-800">
                                    Patient Profile
                                </h2>
                                <span className="text-sm text-gray-500 font-mono bg-gray-200 px-2 py-0.5 rounded text-xs">ID: {selectedPatientId}</span>
                            </div>
                            {loading && <span className="text-xs text-blue-500 font-medium animate-pulse bg-blue-50 px-3 py-1 rounded-full">Syncing live data...</span>}
                        </div>

                        <div className="p-8 overflow-y-auto space-y-8">
                            {/* Profile Sections */}
                            {selectedProfile ? (
                                <div className="grid grid-cols-1 gap-6">
                                    {/* Chief Complaint */}
                                    <div className="bg-white p-6 rounded-xl border border-blue-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                            Chief Complaint
                                        </h3>
                                        {selectedProfile.chief_complaint && selectedProfile.chief_complaint.length > 0 ? (
                                            <div className="flex flex-wrap gap-2">
                                                {selectedProfile.chief_complaint.map((item: any, idx: number) => (
                                                    <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-blue-100">
                                                        {item.value || item}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : <span className="text-gray-400 italic text-sm pl-1">Not recorded</span>}
                                    </div>

                                    {/* Medications */}
                                    <div className="bg-white p-6 rounded-xl border border-green-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-green-500"></div>
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                                            Medications
                                        </h3>
                                        {selectedProfile.medications && selectedProfile.medications.length > 0 ? (
                                            <div className="flex flex-wrap gap-2">
                                                {selectedProfile.medications.map((item: any, idx: number) => (
                                                    <span key={idx} className="bg-green-50 text-green-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-green-100">
                                                        {item.value}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : <span className="text-gray-400 italic text-sm pl-1">None active</span>}
                                    </div>

                                    {/* Symptoms */}
                                    <div className="bg-white p-6 rounded-xl border border-purple-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-shadow">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-purple-500"></div>
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                            Symptoms
                                        </h3>
                                        {selectedProfile.symptoms && selectedProfile.symptoms.length > 0 ? (
                                            <div className="flex flex-wrap gap-2">
                                                {selectedProfile.symptoms.map((item: any, idx: number) => (
                                                    <span key={idx} className="bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-purple-100">
                                                        {item.value}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : <span className="text-gray-400 italic text-sm pl-1">None reported</span>}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-10 text-gray-400">Loading profile data...</div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-300">
                        <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                        <p className="text-lg font-medium">Select a patient to view details</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ClinicianDashboard;
