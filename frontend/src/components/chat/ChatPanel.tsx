import { useState, useRef, useEffect, useImperativeHandle, forwardRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Mic, Phone, Bot, User } from 'lucide-react'
import Button from '../../components/ui/Button'
import Badge, { getRiskVariant } from '../../components/ui/Badge'
import { wellbeingApi, ChatResponse } from '../../api/wellbeing'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface Message {
  id: string
  role: 'user' | 'ai'
  text: string
  tier?: string
  helpline?: string
}

interface ChatPanelProps {
  initialMessage?: string
  className?: string
  onRiskUpdate?: (score: number, tier: string) => void
}

export interface ChatPanelRef {
  addMessage: (msg: Message) => void
  isPending: boolean
}

/* ------------------------------------------------------------------ */
/*  Markdown bold renderer                                             */
/* ------------------------------------------------------------------ */

function renderText(text: string) {
  return text.split(/(\*\*.*?\*\*)/).map((seg, i) =>
    seg.startsWith('**') && seg.endsWith('**')
      ? <strong key={i} className="font-semibold">{seg.slice(2, -2)}</strong>
      : seg
  )
}

/* ------------------------------------------------------------------ */
/*  ChatPanel                                                          */
/* ------------------------------------------------------------------ */

const ChatPanel = forwardRef<ChatPanelRef, ChatPanelProps>(function ChatPanel({ initialMessage, className = '', onRiskUpdate }, ref) {
  const [messages, setMessages] = useState<Message[]>(() => {
    const initial: Message[] = []
    if (initialMessage) {
      initial.push({ id: '0', role: 'ai', text: initialMessage })
    }
    return initial
  })
  const [chatInput, setChatInput] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  /* --- Imperative handle for parent to inject messages -------------- */

  useImperativeHandle(ref, () => ({
    addMessage: (msg: Message) => setMessages((prev) => [...prev, msg]),
    isPending: chatMutation.isPending,
  }))

  /* --- Chat mutation ----------------------------------------------- */

  const chatMutation = useMutation({
    mutationFn: (msg: string) => wellbeingApi.chat(msg),
    onSuccess: (data: ChatResponse, variables: string) => {
      setMessages((prev) => [
        ...prev,
        { id: String(Date.now()), role: 'user', text: variables },
        {
          id: String(Date.now() + 1),
          role: 'ai',
          text: data.reply,
          tier: data.risk_tier,
          helpline: data.helpline,
        },
      ])
      // Update parent's risk assessment on every chat response
      if (data.risk_score != null && data.risk_tier && onRiskUpdate) {
        onRiskUpdate(data.risk_score, data.risk_tier)
      }
    },
  })

  const sendMessage = () => {
    const msg = chatInput.trim()
    if (!msg || chatMutation.isPending) return
    setChatInput('')
    chatMutation.mutate(msg)
  }

  /* --- Render ------------------------------------------------------- */

  return (
    <div className={`flex flex-col bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700/60 overflow-hidden ${className}`}>

      {/* --- Chat Header --------------------------------------------- */}
      <div className="relative px-5 py-4 border-b border-slate-100 dark:border-slate-700/60">
        {/* Subtle gradient accent line */}
        <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#005A70] via-[#007A8D] to-[#005A70]/60" />
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#005A70] to-[#007A8D] flex items-center justify-center shadow-sm">
            <Bot size={18} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">NexusAI Companion</p>
            <p className="text-xs text-slate-400 dark:text-slate-500">AI-powered wellbeing support</p>
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs text-green-600 bg-green-50 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Online
          </span>
        </div>
      </div>

      {/* --- Messages ------------------------------------------------ */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/30 dark:bg-slate-900/30">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                msg.role === 'user'
                  ? 'bg-[#005A70] shadow-sm'
                  : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-sm'
              }`}
            >
              {msg.role === 'user' ? (
                <User size={13} className="text-white" />
              ) : (
                <Bot size={13} className="text-[#005A70] dark:text-teal-300" />
              )}
            </div>

            {/* Bubble + meta */}
            <div className={`max-w-[78%] flex flex-col gap-1.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div
                className={`rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#005A70] text-white rounded-tr-md shadow-sm'
                    : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-tl-md shadow-sm border border-slate-100 dark:border-slate-600'
                }`}
              >
                {renderText(msg.text)}
              </div>

              {/* Tier badge */}
              {msg.tier && (
                <Badge variant={getRiskVariant(msg.tier)} className="text-[10px]">
                  {msg.tier} risk
                </Badge>
              )}

              {/* Helpline alert */}
              {msg.helpline && (
                <div className="flex items-center gap-1.5 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  <Phone size={12} />
                  <span>iCall Helpline: <strong>{msg.helpline}</strong></span>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {chatMutation.isPending && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-sm flex items-center justify-center">
              <Bot size={13} className="text-[#005A70] dark:text-teal-300" />
            </div>
            <div className="bg-white dark:bg-slate-700 border border-slate-100 dark:border-slate-600 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-[#005A70]/40 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* --- Input Area ---------------------------------------------- */}
      <div className="p-4 border-t border-slate-100 dark:border-slate-700/60 bg-white dark:bg-slate-800">
        <div className="flex gap-2 items-end">
          <button
            className="text-slate-400 hover:text-[#005A70] dark:hover:text-teal-300 transition-colors p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700"
            title="Voice input"
          >
            <Mic size={18} />
          </button>
          <div className="flex-1">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Type a message... (Enter to send)"
              rows={1}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50/50 dark:bg-slate-700/50 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-200
                placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-[#005A70]/20 focus:border-[#005A70]
                focus:bg-white dark:focus:bg-slate-700 resize-none transition-all"
            />
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={sendMessage}
            disabled={!chatInput.trim() || chatMutation.isPending}
            className="px-3 py-2.5 rounded-xl"
            icon={<Send size={15} />}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  )
})

export default ChatPanel
