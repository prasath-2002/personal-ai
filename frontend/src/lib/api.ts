const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

if (!API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is not configured"
  );
}


export type Session = {
  session_id: string;
  title: string;
  created_at: string;
};


export type Message = {
  role: "user" | "assistant";
  content: string;
};


export type UploadResult = {
  session_id: string;
  document_id: number;
  filename: string;
  characters: number;
  chunks: number;
  preview: string;
};


export type DocumentItem = {
  document_id: number;
  filename: string;
  created_at: string;
};


async function handleResponse(
  response: Response
): Promise<Response> {
  if (!response.ok) {
    let errorMessage = "";
    const body = await response.text();

    try {
      const data = JSON.parse(body);

      errorMessage =
        (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) ||
        JSON.stringify(data);
    } catch {
      errorMessage =
        body;
    }

    throw new Error(
      errorMessage ||
        `Request failed with status ${response.status}`
    );
  }

  return response;
}

// ========================================
// Sessions
// ========================================

export async function getSessions(): Promise<
  Session[]
> {
  const response = await fetch(
    `${API_URL}/sessions`
  );

  await handleResponse(response);

  const data =
    await response.json();

  return data.sessions;
}


export async function renameSession(
  sessionId: string,
  title: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/sessions/${encodeURIComponent(
      sessionId
    )}`,
    {
      method: "PATCH",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        title,
      }),
    }
  );

  await handleResponse(response);
}


export async function deleteSession(
  sessionId: string
): Promise<void> {
  const response = await fetch(
    `${API_URL}/sessions/${encodeURIComponent(
      sessionId
    )}`,
    {
      method: "DELETE",
    }
  );

  await handleResponse(response);
}


// ========================================
// History
// ========================================

export async function getHistory(
  sessionId: string
): Promise<Message[]> {
  const response = await fetch(
    `${API_URL}/history/${encodeURIComponent(
      sessionId
    )}`
  );

  await handleResponse(response);

  const data =
    await response.json();

  return data.messages;
}

export async function clearHistory(sessionId: string): Promise<void> {
  await handleResponse(await fetch(`${API_URL}/reset?session_id=${encodeURIComponent(sessionId)}`, { method: "POST" }));
}


// ========================================
// Streaming Chat
// ========================================

export async function streamChat(
  sessionId: string,
  message: string,
  signal?: AbortSignal
): Promise<Response> {
  const response = await fetch(
    `${API_URL}/chat/stream`,
    {
      method: "POST",
      signal,

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    }
  );

  await handleResponse(response);

  return response;
}


// ========================================
// Upload
// ========================================

export async function uploadFile(
  sessionId: string,
  file: File
): Promise<UploadResult> {
  const formData =
    new FormData();

  formData.append(
    "session_id",
    sessionId
  );

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_URL}/files/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  await handleResponse(response);

  return response.json();
}


// ========================================
// Documents
// ========================================

export async function getDocuments(
  sessionId: string
): Promise<DocumentItem[]> {
  const response = await fetch(
    `${API_URL}/documents/${encodeURIComponent(
      sessionId
    )}`
  );

  await handleResponse(response);

  const data =
    await response.json();

  return data.documents;
}


export async function deleteDocument(
  documentId: number
): Promise<void> {
  const response = await fetch(
    `${API_URL}/documents/${documentId}`,
    {
      method: "DELETE",
    }
  );

  await handleResponse(response);
}

export type AppConfig = {
  llm_provider: string;
  configured: boolean;
  max_upload_bytes: number;
};

export async function getConfig(): Promise<AppConfig> {
  const response = await fetch(
    `${API_URL}/config`
  );

  await handleResponse(response);

  return response.json();
}
