import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Add cache busting parameter
    const response = await fetch(`http://localhost:8000/agents?t=${Date.now()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      {
        agents: [
          {
            name: "general-assistant",
            role: "General Assistant",
            description: "A helpful, concise assistant providing clear answers",
          },
          {
            name: "technical-assistant",
            role: "Developer Assistant",
            description: "Expert developer assistant providing code examples and technical advice",
          },
          {
            name: "creative-writer",
            role: "Creative Writer",
            description: "Creative writing assistant producing vivid, original text",
          },
          {
            name: "fact-checker",
            role: "Fact Checker",
            description: "Careful fact-checker verifying claims with sources",
          },
          {
            name: "tutor",
            role: "Tutor",
            description: "Patient tutor explaining concepts with examples",
          },
        ]
      },
      { status: 200 }
    );
  }
}