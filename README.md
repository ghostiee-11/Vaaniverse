# VaaniVerse: The Inclusive Multimodal AI Companion

VaaniVerse is an AI-powered, voice-first, multimodal platform designed to bridge language, literacy, and accessibility barriers. It enables access to public services, mentorship, and travel guidance through simple voice calls, SMS, or WhatsApp messages—without requiring apps, typing, or high-end devices.

## Overview

VaaniVerse provides a unified gateway that supports three major user needs:

- Travel exploration using voice-guided experiences
- Navigation of government welfare schemes
- Access to mentorship for rural youth

Each use case is handled by a specialized AI agent within a shared ecosystem. The platform is multilingual, device-agnostic, and works offline.

## Problem Statements Addressed

1. Build the voice of the city for travelers
2. Create a digital companion for accessing welfare
3. Develop a voice-first mentorship platform for rural youth

## Core Use Cases and AI Agents

| Use Case                  | Target User             | AI Agent           |
|---------------------------|-------------------------|--------------------|
| Travel guidance           | Urban travelers         | Travel Agent       |
| Social welfare support    | Welfare beneficiaries   | Welfare Agent      |
| Mentorship access         | Rural youth             | MentorMatch Agent  |

## Key Features

- Voice-first interface using calls, voice notes, and IVR
- Multilingual support for regional and mixed languages
- Context-aware and emotion-sensitive conversations
- Personalized storytelling and recommendations
- Document-free access via voice authentication
- Real-time routing to human support when needed
- Support for sign language and lip reading
- Works on low-end phones without internet

## System Architecture

- Modular AI agents with shared memory and persona context
- Central router orchestrating all user intents
- Retrieval augmented generation for updated information
- Built-in safety, moderation, and fallback mechanisms
- Integration with WhatsApp, SMS, and phone networks

## Technology Stack

| Category            | Tools and Libraries                               |
|---------------------|---------------------------------------------------|
| Language Models     | GPT-4o, Claude, Mistral, HuggingFace, LaBSE       |
| Agent Frameworks    | LangChain, CrewAI, LangGraph                      |
| Search and RAG      | FAISS, Pinecone, CSV, PDF, Markdown               |
| Speech Processing   | Whisper, Faster Whisper, Bhashini, Coqui TTS      |
| Multimodal Input    | PaddleOCR, MediaPipe, LipNet, EasyOCR             |
| Frontend            | Streamlit, Flask                                  |
| Communication       | Twilio, WhatsApp Cloud API, Telegram API          |
| Backend             | FastAPI, Redis                                    |
| Moderation Tools    | Detoxify, Perspective API                         |

## Project Structure

vaaniverse/
- backend              API logic and routing
- agents               Travel, Welfare, MentorMatch, Story modules
- core                 Router, memory, and context handling
- data                 RAG-ready documents and datasets
- frontend             Streamlit-based interface
- utils                Logging and moderation
- assets               PDFs and diagrams
- README.md            Project documentation

## Highlights

- Solves three real-world problems with one shared system
- Offline-first, multilingual, and accessible design
- Scalable AI architecture using modular agents
