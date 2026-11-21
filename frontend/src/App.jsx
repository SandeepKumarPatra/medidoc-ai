import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import PolicyQA from './screens/PolicyQA';
import DocumentExtraction from './screens/DocumentExtraction';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('qa');

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800">
      {/* App Sidebar Shell */}
      <Sidebar activeScreen={activeScreen} onSelectScreen={setActiveScreen} />

      {/* Dynamic Screen View */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {activeScreen === 'qa' && <PolicyQA />}
        {activeScreen === 'extract' && <DocumentExtraction />}
      </div>
    </div>
  );
}
