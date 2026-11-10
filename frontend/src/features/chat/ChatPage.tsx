import { useState, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiRequest } from "@/lib/api/client";

interface ChatMessage {
  role: "user" | "model";
  content: string;
}

interface ChatResponse {
  message: string;
  model: string;
}

const starter: ChatMessage = {
  role: "model",
  content:
    "Soy SentinelAI Copilot. Puedo ayudarte a interpretar señales de riesgo, preparar una revisión y explicar el comportamiento del modelo.",
};

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([starter]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending) return;

    const nextMessages = [...messages, { role: "user" as const, content: message }];
    setMessages(nextMessages);
    setDraft("");
    setError(null);
    setIsSending(true);
    try {
      const response = await apiRequest<ChatResponse>("/api/v1/chat", {
        method: "POST",
        body: { message, history: messages.slice(-12) },
      });
      setMessages([...nextMessages, { role: "model", content: response.message }]);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "No se pudo contactar a Gemini.",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="chat-page" aria-labelledby="chat-title">
      <div className="chat-intro">
        <div>
          <p className="section-kicker">Fraud operations assistant</p>
          <h1 id="chat-title">AI Copilot</h1>
          <p>Consulta señales, riesgos y próximos pasos con el contexto de tu operación.</p>
        </div>
        <span className="chat-model-badge"><Icon name="message" size={15} /> Gemini</span>
      </div>

      <div className="chat-panel card">
        <div className="chat-messages" aria-live="polite">
          {messages.map((item, index) => (
            <div className={`chat-message ${item.role}`} key={`${item.role}-${index}`}>
              <span className="chat-message-label">{item.role === "model" ? "Copilot" : "Tú"}</span>
              <p>{item.content}</p>
            </div>
          ))}
          {isSending && <div className="chat-typing" role="status">Copilot está escribiendo…</div>}
        </div>
        <form className="chat-composer" onSubmit={handleSubmit}>
          <label htmlFor="chat-message">Mensaje</label>
          <textarea
            id="chat-message"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ej. ¿Qué señales debería revisar en una transacción de alto riesgo?"
            maxLength={4000}
            rows={3}
            disabled={isSending}
          />
          <div className="chat-composer-footer">
            <span>{error ?? "No compartas credenciales ni datos personales sensibles."}</span>
            <button className="button button-primary" type="submit" disabled={!draft.trim() || isSending}>
              <Icon name="arrow" size={16} /> Enviar
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}