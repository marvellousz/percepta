'use client';

import { useEffect, useState } from 'react';
import LiveKitChat from '@/components/LiveKitChat';
import { useRouter } from 'next/navigation';

interface RoomPageProps {
  params: {
    roomId: string;
  };
}

export default function RoomPage({ params }: RoomPageProps) {
  const router = useRouter();
  const [username, setUsername] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  
  // Get room ID from params
  const roomId = params.roomId;
  
  // On component mount, check if we have a username in session storage
  useEffect(() => {
    const storedUsername = sessionStorage.getItem('username');
    if (!storedUsername) {
      // No username, redirect to login
      router.push('/login');
    } else {
      setUsername(storedUsername);
      setIsLoading(false);
    }
  }, [router]);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Room: {roomId}</h1>
        <button 
          onClick={() => router.push('/')}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
        >
          Leave Room
        </button>
      </div>
      
      <div className="h-[70vh]">
        <LiveKitChat username={username} roomName={roomId} />
      </div>
    </div>
  );
}
