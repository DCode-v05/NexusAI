import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, StickyNote, X, MessageSquare, Clock } from 'lucide-react'
import Button from '../../components/ui/Button'
import Badge, { getRiskVariant } from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { counselorApi, AlertCard } from '../../api/counselor'

function anonLabel(_alertId: number, index?: number): string {
  return `Case ${index != null ? index + 1 : _alertId}`
}

export default function CounselorDashboard() {
  const qc = useQueryClient()
  const [selectedAlert, setSelectedAlert] = useState<AlertCard | null>(null)
  const [noteText, setNoteText] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)
  const [resolvedMsg, setResolvedMsg] = useState('')

  useEffect(() => {
    if (!resolvedMsg) return
    const timer = setTimeout(() => setResolvedMsg(''), 4000)
    return () => clearTimeout(timer)
  }, [resolvedMsg])

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['counselor-alerts'],
    queryFn: () => counselorApi.getAlerts(0.3),
    refetchInterval: 30_000,
  })

  // Keep selectedAlert in sync with latest data
  useEffect(() => {
    if (selectedAlert) {
      const updated = alerts.find(a => a.alert_id === selectedAlert.alert_id)
      if (updated) setSelectedAlert(updated)
    }
  }, [alerts])

  const addNoteMutation = useMutation({
    mutationFn: () => counselorApi.addNote(selectedAlert!.alert_id, noteText),
    onSuccess: () => {
      setNoteText('')
      qc.invalidateQueries({ queryKey: ['counselor-alerts'] })
    },
  })

  const resolveMutation = useMutation({
    mutationFn: () => counselorApi.resolveAlert(selectedAlert!.alert_id, noteText),
    onSuccess: () => {
      setShowConfirm(false)
      setSelectedAlert(null)
      setNoteText('')
      setResolvedMsg('Case resolved. Anonymous notification sent to the student.')
      qc.invalidateQueries({ queryKey: ['counselor-alerts'] })
    },
  })

  const open = alerts.filter((a) => !a.is_resolved)
  const resolved = alerts.filter((a) => a.is_resolved)

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-8rem)]">
      {resolvedMsg && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700/60 text-emerald-700 dark:text-emerald-300 text-sm font-medium">
          <CheckCircle2 size={16} />
          {resolvedMsg}
        </div>
      )}
      <div className="grid grid-cols-5 gap-6 flex-1 min-h-0">
      {/* Left: Risk feed */}
      <div className="col-span-2 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Active Alerts <span className="ml-1.5 text-xs text-slate-400 font-normal">({open.length})</span>
          </h3>
        </div>
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center"><Spinner /></div>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {open.length === 0 && (
              <div className="text-center py-12 text-slate-400 text-sm">
                <CheckCircle2 size={32} className="mx-auto mb-2 text-success" />
                No active alerts
              </div>
            )}
            {open.map((alert, idx) => (
              <button
                key={alert.alert_id}
                onClick={() => setSelectedAlert(alert)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  selectedAlert?.alert_id === alert.alert_id
                    ? 'border-[#005A70] bg-[#005A70]/5 shadow-sm dark:bg-[#005A70]/10'
                    : 'border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle
                      size={15}
                      className={
                        alert.tier === 'crisis' ? 'text-error' :
                        alert.tier === 'high' ? 'text-orange-500' : 'text-warning'
                      }
                    />
                    <span className="text-sm font-medium text-slate-800 dark:text-slate-100">
                      {anonLabel(alert.alert_id, idx)}
                    </span>
                  </div>
                  <Badge variant={getRiskVariant(alert.tier)}>{alert.tier}</Badge>
                </div>
                {/* Show trigger message preview */}
                {alert.trigger_message && (
                  <p className="mt-1.5 text-xs text-slate-600 dark:text-slate-300 line-clamp-2 italic">
                    "{alert.trigger_message}"
                  </p>
                )}
                <div className="mt-2 flex gap-3 text-xs text-slate-500 dark:text-slate-400">
                  <span>Risk: <strong className="text-slate-700 dark:text-slate-200">{(alert.risk_score * 100).toFixed(0)}%</strong></span>
                  <span>Anomaly: <strong className="text-slate-700 dark:text-slate-200">{(alert.anomaly_score * 100).toFixed(0)}%</strong></span>
                </div>
                <p className="mt-1.5 text-[10px] text-slate-400">
                  {new Date(alert.created_at).toLocaleDateString('en-IN', {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                  })}
                </p>
              </button>
            ))}

            {resolved.length > 0 && (
              <div className="pt-2">
                <p className="text-xs text-slate-400 font-medium mb-2">Resolved ({resolved.length})</p>
                {resolved.slice(0, 3).map((alert, rIdx) => (
                  <div key={alert.alert_id} className="p-3 rounded-xl border border-slate-100 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-900 mb-2 opacity-60">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-600 dark:text-slate-300">{anonLabel(alert.alert_id, rIdx)}</span>
                      <CheckCircle2 size={14} className="text-success" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: Case detail */}
      <div className="col-span-3 flex flex-col overflow-hidden">
        {selectedAlert ? (
          <div className="flex flex-col h-full bg-white dark:bg-slate-800 rounded-xl shadow-card border border-slate-200 dark:border-slate-700/60 overflow-hidden">
            {/* Header */}
            <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                  {anonLabel(selectedAlert.alert_id, open.findIndex(a => a.alert_id === selectedAlert.alert_id))}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Anonymous Case Report</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={getRiskVariant(selectedAlert.tier)}>{selectedAlert.tier}</Badge>
                <button onClick={() => setSelectedAlert(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto">
              {/* Metrics */}
              <div className="p-5 border-b border-slate-100 dark:border-slate-700/60">
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'Risk Score', value: `${(selectedAlert.risk_score * 100).toFixed(0)}%` },
                    { label: 'Anomaly', value: `${(selectedAlert.anomaly_score * 100).toFixed(0)}%` },
                    { label: 'Sentiment', value: `${(selectedAlert.sentiment_score * 100).toFixed(0)}%` },
                  ].map((m) => (
                    <div key={m.label} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 text-center">
                      <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{m.value}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{m.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Trigger message */}
              {selectedAlert.trigger_message && (
                <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700/60">
                  <div className="flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
                    <MessageSquare size={14} />
                    Student's Message (Anonymous)
                  </div>
                  <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40">
                    <p className="text-sm text-slate-700 dark:text-slate-200 italic">"{selectedAlert.trigger_message}"</p>
                  </div>
                </div>
              )}

              {/* Existing case notes */}
              {selectedAlert.notes?.length > 0 && (
                <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700/60">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-1.5">
                    <Clock size={14} />
                    Previous Notes ({selectedAlert.notes.length})
                  </p>
                  <div className="space-y-2">
                    {selectedAlert.notes.map((note) => (
                      <div key={note.id} className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/60">
                        <p className="text-sm text-slate-700 dark:text-slate-300">{note.note_text}</p>
                        <p className="text-[10px] text-slate-400 mt-1.5">
                          {new Date(note.created_at).toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                          })}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* New note input */}
              <div className="p-5">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-200 flex items-center gap-1.5 mb-2">
                  <StickyNote size={14} />
                  Add Case Note
                </label>
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Write your observations about this case..."
                  rows={4}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-600 px-4 py-3 text-sm text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-[#005A70]/30 focus:border-[#005A70] resize-none"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="px-5 py-4 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowConfirm(true)}
                disabled={selectedAlert.is_resolved}
              >
                Resolve Case
              </Button>
              <Button
                variant="primary"
                icon={<StickyNote size={15} />}
                loading={addNoteMutation.isPending}
                disabled={!noteText.trim()}
                onClick={() => addNoteMutation.mutate()}
              >
                Add Note
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
            <div className="text-center">
              <AlertTriangle size={36} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
              <p>Select an alert to view details</p>
            </div>
          </div>
        )}
      </div>

      </div>

      {/* Confirm modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-sm w-full p-6">
            <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 mb-2">Resolve this case?</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
              The case will be marked as resolved and the student will receive an anonymous notification from the counselor.
            </p>
            <div className="flex gap-3 justify-end">
              <Button variant="ghost" onClick={() => setShowConfirm(false)}>Cancel</Button>
              <Button
                variant="destructive"
                loading={resolveMutation.isPending}
                onClick={() => resolveMutation.mutate()}
              >
                Confirm Resolve
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
