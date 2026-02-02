import { useState, useEffect } from 'react';

interface ProfileItem {
    value: string;
    status: string;
    provenance_pointer: number;
    updated_at: string;
}

interface PatientProfile {
    chief_complaint: ProfileItem[];
    medications: ProfileItem[];
    symptoms: ProfileItem[];
    allergies: ProfileItem[];
    last_updated: string;
}

interface PatientProfileSidebarProps {
    token: string;
}

const PatientProfileSidebar: React.FC<PatientProfileSidebarProps> = ({ token }) => {
    const [profile, setProfile] = useState<PatientProfile | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const response = await fetch('/api/v1/chat/patient/profile', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setProfile(data);
                }
            } catch (error) {
                console.error("Failed to fetch profile", error);
            }
        };

        fetchProfile();
        // Poll every 3 seconds for live updates
        const interval = setInterval(fetchProfile, 3000);
        return () => clearInterval(interval);
    }, [token]);

    if (!profile) return <div className="p-4 text-gray-500">Loading Profile...</div>;

    const renderSection = (title: string, items: ProfileItem[]) => (
        <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-2 border-b pb-1">{title}</h3>
            {items.length === 0 ? (
                <p className="text-xs text-gray-400 italic">None recorded</p>
            ) : (
                <ul className="space-y-2">
                    {items.map((item, idx) => (
                        <li key={idx} className="bg-white p-2 rounded shadow-sm border border-gray-100 flex justify-between items-center">
                            <div>
                                <span className="text-sm font-medium text-gray-800 block">{item.value}</span>
                                <span className="text-xs text-gray-500">Updated: {new Date(item.updated_at).toLocaleTimeString()}</span>
                            </div>
                            <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${item.status === 'active' ? 'bg-green-100 text-green-800' :
                                item.status === 'past' || item.status === 'stopped' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                                }`}>
                                {item.status}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );

    return (
        <div className="w-80 bg-gray-50 border-l border-gray-200 p-4 h-[calc(100vh-8rem)] overflow-y-auto hidden lg:block">
            <h2 className="text-lg font-bold text-blue-900 mb-4">Patient Profile</h2>

            {renderSection("Chief Complaint", profile.chief_complaint)}
            {renderSection("Medications", profile.medications)}
            {renderSection("Symptoms", profile.symptoms)}
            {renderSection("Allergies", profile.allergies)}

            <div className="mt-8 pt-4 border-t text-xs text-gray-400">
                Last Sync: {new Date().toLocaleTimeString()}
            </div>
        </div>
    );
};

export default PatientProfileSidebar;
