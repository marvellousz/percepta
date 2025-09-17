import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/agents', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
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
            name: "support-agent",
            role: "Customer Support",
            description: "Helps with technical issues",
          },
          {
            name: "sales-agent",
            role: "Sales Representative",
            description: "Provides product information",
          },
          {
            name: "advisor-agent",
            role: "Financial Advisor",
            description: "Offers financial guidance",
          },
        ]
      },
      { status: 200 }
    );
  }
}