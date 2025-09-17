// frontend/src/pages/index.tsx
import React, { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import { DEMO_ROOM } from '../constants';
import Head from 'next/head';

import styles from '../styles/Home.module.css';

export default function Home() {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!username.trim()) {
      setError('Username is required');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Validate the username with the backend
      const response = await fetch('/api/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, room: DEMO_ROOM }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to validate username: ${response.statusText}`);
      }
      
      // Navigate to the chat room
      router.push({
        pathname: `/room/${DEMO_ROOM}`,
        query: { username },
      });
    } catch (err) {
      console.error('Error:', err);
      setError(err instanceof Error ? err.message : 'Failed to join room');
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>MemoryBot Chat</title>
        <meta name="description" content="Chat with MemoryBot" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to <span className={styles.highlight}>MemoryBot</span>
        </h1>
        
        <p className={styles.description}>
          Chat with an AI assistant that remembers your conversations
        </p>
        
        <div className={styles.formContainer}>
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label htmlFor="username" className={styles.label}>
                Enter your username to join the chat
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Your username"
                className={styles.input}
                autoComplete="off"
                disabled={isLoading}
              />
            </div>
            
            {error && <div className={styles.error}>{error}</div>}
            
            <button 
              type="submit" 
              className={styles.button}
              disabled={isLoading || !username.trim()}
            >
              {isLoading ? 'Joining...' : 'Join Chat'}
            </button>
          </form>
        </div>
      </main>

      <footer className={styles.footer}>
        <p>
          Powered by LiveKit, mem0, and Google Gemini
        </p>
      </footer>
    </div>
  );
}
