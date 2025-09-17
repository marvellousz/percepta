import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch('http://localhost:8000/handoff', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in agent handoff:', error);
    return NextResponse.json(
      { 
        success: false,
        message: "I'm having trouble switching agents right now. Please try again later.",
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

