// frontend/src/pages/room/[room].tsx
import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Chat from '../../components/Chat';
import { DEMO_ROOM } from '../../constants';

import styles from '../../styles/Room.module.css';

export default function RoomPage() {
  const router = useRouter();
  const { room, username } = router.query;
  
  // Redirect to home if no username
  useEffect(() => {
    if (router.isReady && !username) {
      router.replace('/');
    }
  }, [router.isReady, username, router]);
  
  // Show loading while router is not ready or redirecting
  if (!router.isReady || !username) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingText}>Loading...</div>
      </div>
    );
  }
  
  // Ensure room is always DEMO_ROOM for security
  const safeRoom = DEMO_ROOM;
  // Ensure username is a string
  const safeUsername = typeof username === 'string' ? username : Array.isArray(username) ? username[0] : '';
  
  // Redirect if username is empty after processing
  if (!safeUsername) {
    // Use useEffect for client-side redirect to avoid hydration issues
    useEffect(() => {
      router.replace('/');
    }, [router]);
    
    return (
      <div className={styles.loading}>
        <div className={styles.loadingText}>Redirecting...</div>
      </div>
    );
  }
  
  return (
    <div className={styles.container}>
      <Head>
        <title>Chat Room: {safeRoom}</title>
        <meta name="description" content={`Chat room ${safeRoom}`} />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <main className={styles.main}>
        <Chat username={safeUsername} roomName={safeRoom} />
      </main>
      
      <footer className={styles.footer}>
        <button 
          className={styles.leaveButton}
          onClick={() => router.push('/')}
        >
          Leave Room
        </button>
      </footer>
    </div>
  );
}
