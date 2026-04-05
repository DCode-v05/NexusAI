import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Upload, X, Rocket, CheckCircle2, ChevronRight, FileText, Target, Briefcase, ArrowLeft, ExternalLink, MapPin, DollarSign } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import ChatPanel from '../../components/chat/ChatPanel'
import SkillRadarChart from '../../components/charts/SkillRadarChart'
import { pathwayApi, SkillProfile, RoadmapResponse, JobOpening } from '../../api/pathway'

type Step = 1 | 2 | 3
type Step3View = 'openings' | 'roadmap'

function renderRoadmap(text: string) {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // ### Week X: Title -> styled week headers
    const weekMatch = line.match(/^###\s+Week\s+(\d+):\s*(.*)/)
    if (weekMatch) {
      elements.push(
        <div key={i} className="mt-5 mb-2 flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-[#005A70]/10 flex items-center justify-center text-[#005A70] dark:text-teal-400 font-bold text-xs shrink-0">
            W{weekMatch[1]}
          </div>
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            {formatInline(weekMatch[2])}
          </h4>
        </div>
      )
      continue
    }

    // - Item -> list items with bullet dots
    const listMatch = line.match(/^[-*]\s+(.*)/)
    if (listMatch) {
      elements.push(
        <div key={i} className="flex items-start gap-2 ml-4 mb-1">
          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#005A70]/50 shrink-0" />
          <span className="text-sm text-slate-600 dark:text-slate-300">{formatInline(listMatch[1])}</span>
        </div>
      )
      continue
    }

    // Empty line
    if (line.trim() === '') {
      elements.push(<div key={i} className="h-2" />)
      continue
    }

    // Regular paragraph
    elements.push(
      <p key={i} className="text-sm text-slate-700 dark:text-slate-200 mb-1">
        {formatInline(line)}
      </p>
    )
  }

  return <div>{elements}</div>
}

function formatInline(text: string): React.ReactNode {
  // Process **bold**, [text](url) inline formatting
  const parts: React.ReactNode[] = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Check for [text](url) links
    const linkMatch = remaining.match(/^(.*?)\[([^\]]+)\]\(([^)]+)\)(.*)/)
    if (linkMatch) {
      if (linkMatch[1]) {
        parts.push(...parseBold(linkMatch[1], key))
        key += 10
      }
      parts.push(
        <a
          key={`link-${key++}`}
          href={linkMatch[3]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#005A70] dark:text-teal-400 underline hover:text-[#004557] dark:hover:text-teal-300"
        >
          {linkMatch[2]}
        </a>
      )
      remaining = linkMatch[4]
      continue
    }

    // No more links, parse bold in remainder
    parts.push(...parseBold(remaining, key))
    break
  }

  return parts.length === 1 ? parts[0] : <>{parts}</>
}

function parseBold(text: string, startKey: number): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  const boldRegex = /\*\*([^*]+)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let key = startKey

  while ((match = boldRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<span key={`t-${key++}`}>{text.slice(lastIndex, match.index)}</span>)
    }
    parts.push(<strong key={`b-${key++}`} className="font-semibold text-slate-800 dark:text-slate-100">{match[1]}</strong>)
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    parts.push(<span key={`t-${key++}`}>{text.slice(lastIndex)}</span>)
  }

  return parts
}

export default function PathwayAIPage() {
  const [step, setStep] = useState<Step>(1)
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [skills, setSkills] = useState<SkillProfile | null>(null)
  const [targetRole, setTargetRole] = useState('Software Engineer')
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null)
  const [jobOpenings, setJobOpenings] = useState<JobOpening[]>([])
  const [step3View, setStep3View] = useState<Step3View>('roadmap')
  const fileRef = useRef<HTMLInputElement>(null)

  const uploadMutation = useMutation({
    mutationFn: (f: File) => pathwayApi.uploadResume(f),
    onSuccess: (data) => {
      setSkills(data)
      setTargetRole(data.target_role || 'Software Engineer')
      setStep(2)
    },
  })

  const roadmapMutation = useMutation({
    mutationFn: () => pathwayApi.generateRoadmap(skills?.skills ?? [], targetRole),
    onSuccess: (data) => {
      setRoadmap(data)
      setStep3View('roadmap')
      setStep(3)
    },
  })

  const openingsMutation = useMutation({
    mutationFn: () => pathwayApi.getJobOpenings(skills?.skills ?? [], targetRole),
    onSuccess: (data) => {
      setJobOpenings(data)
      setStep3View('openings')
      setStep(3)
    },
  })

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  // Deterministic score per skill (0-16 bit hash → 4–8 range); stable across renders
  const _hashSkill = (s: string): number => {
    let h = 0
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xffff
    return (h % 5) + 4
  }
  const skillData = (skills?.skills ?? ['Python', 'React', 'SQL', 'ML', 'Docker']).slice(0, 6).map((s) => ({
    skill: s,
    current: _hashSkill(s),
    required: 8,
  }))

  // Only show step 3 in stepper once the user has made a choice
  const steps = step === 3
    ? [
        { n: 1, label: 'Upload Resume' },
        { n: 2, label: 'Review Skills' },
        { n: 3, label: step3View === 'openings' ? 'Job Openings' : 'Your Roadmap' },
      ]
    : [
        { n: 1, label: 'Upload Resume' },
        { n: 2, label: 'Review Skills' },
      ]

  return (
    <div className="grid grid-cols-5 gap-5 h-[calc(100vh-8rem)]">

      {/* LEFT PANEL: CAREER TOOLS (Resume -> Skills -> Roadmap/Openings) */}
      <div className="col-span-2 flex flex-col gap-4 overflow-y-auto scrollbar-thin pr-1">

        {/* Stepper */}
        <div className="flex items-center justify-center gap-0 bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700/60 px-4 py-3">
          {steps.map((s, idx) => (
            <div key={s.n} className="flex items-center">
              <div className="flex items-center gap-1.5">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${
                    step > s.n
                      ? 'bg-success text-white'
                      : step === s.n
                      ? 'bg-[#005A70] text-white'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {step > s.n ? <CheckCircle2 size={14} /> : s.n}
                </div>
                <span
                  className={`text-xs font-medium ${
                    step === s.n ? 'text-[#005A70] dark:text-teal-400' : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {s.label}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <ChevronRight size={14} className="text-slate-300 dark:text-slate-600 mx-2" />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Upload */}
        {step === 1 && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700/60 overflow-hidden">
            <div className="bg-gradient-to-r from-[#005A70] to-[#007A8D] px-5 py-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                  <FileText size={16} className="text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Upload Your Resume</h3>
                  <p className="text-xs text-white/70">PDF or DOCX, max 5MB</p>
                </div>
              </div>
            </div>

            <div className="p-5">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all ${
                  dragOver
                    ? 'border-[#005A70] bg-[#005A70]/5'
                    : file
                    ? 'border-success bg-green-50 dark:bg-green-900/20'
                    : 'border-slate-300 dark:border-slate-600 hover:border-[#005A70] hover:bg-slate-50 dark:hover:bg-slate-900'
                }`}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
                <Upload size={32} className={file ? 'text-success' : 'text-slate-400'} />
                {file ? (
                  <div className="mt-3 text-center">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{file.name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{(file.size / 1024).toFixed(0)} KB</p>
                    <button
                      onClick={(e) => { e.stopPropagation(); setFile(null) }}
                      className="mt-2 text-xs text-error hover:underline flex items-center gap-1 mx-auto"
                    >
                      <X size={12} /> Remove
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 text-center">
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Drop your resume here</p>
                    <p className="text-xs text-slate-400 mt-1">or click to browse</p>
                  </div>
                )}
              </div>

              <Button
                variant="primary"
                size="lg"
                icon={<Rocket size={16} />}
                loading={uploadMutation.isPending}
                disabled={!file}
                onClick={() => file && uploadMutation.mutate(file)}
                className="w-full mt-4 rounded-xl"
              >
                Analyse Resume
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Review skills */}
        {step === 2 && skills && (
          <div className="space-y-4">
            <Card title="Your Skill Profile" subtitle="Extracted from your resume">
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">Detected Skills</p>
                <div className="flex flex-wrap gap-2">
                  {skills.skills.map((s) => (
                    <span
                      key={s}
                      className="px-3 py-1.5 rounded-full text-xs font-medium bg-[#005A70]/10 text-[#005A70] dark:text-teal-400 border border-[#005A70]/20"
                    >
                      {s}
                    </span>
                  ))}
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">Target Role</label>
                  <input
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#005A70]/30 focus:border-[#005A70]"
                  />
                </div>
                <div className="mt-4">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">Skill Gap Analysis</p>
                  <SkillRadarChart data={skillData} />
                </div>
              </div>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="secondary"
                size="lg"
                icon={<Briefcase size={16} />}
                loading={openingsMutation.isPending}
                onClick={() => openingsMutation.mutate()}
                className="flex-1 rounded-xl"
              >
                Get Job Openings
              </Button>
              <Button
                variant="primary"
                size="lg"
                icon={<Target size={16} />}
                loading={roadmapMutation.isPending}
                onClick={() => roadmapMutation.mutate()}
                className="flex-1 rounded-xl"
              >
                Generate 12-Week Roadmap
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Roadmap or Job Openings */}
        {step === 3 && (
          <div className="space-y-4">

            {/* Openings view */}
            {step3View === 'openings' && (
              <Card title="Job Openings" subtitle={`Matching your skills for ${targetRole}`}>
                {jobOpenings.length > 0 ? (
                  <div className="space-y-3">
                    {jobOpenings.map((job, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-100 dark:border-slate-700/60 hover:border-[#005A70]/30 transition-colors bg-white dark:bg-slate-800/50"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{job.role}</h4>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{job.company}</p>
                          </div>
                          {job.demand_score != null && (
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold shrink-0 ${
                              job.demand_score >= 0.7
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                : job.demand_score >= 0.4
                                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                                : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                            }`}>
                              {(job.demand_score * 100).toFixed(0)}% demand
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 dark:text-slate-400">
                          {job.location && (
                            <span className="flex items-center gap-1">
                              <MapPin size={12} /> {job.location}
                            </span>
                          )}
                          {(job.min_salary_lpa != null || job.max_salary_lpa != null) && (
                            <span className="flex items-center gap-1">
                              <DollarSign size={12} />
                              {job.min_salary_lpa != null && job.max_salary_lpa != null
                                ? `${job.min_salary_lpa} - ${job.max_salary_lpa} LPA`
                                : job.min_salary_lpa != null
                                ? `${job.min_salary_lpa}+ LPA`
                                : `Up to ${job.max_salary_lpa} LPA`}
                            </span>
                          )}
                          {job.experience_level && (
                            <span className="text-xs">{job.experience_level}</span>
                          )}
                        </div>

                        {job.required_skills?.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2.5">
                            {job.required_skills.map((skill) => (
                              <span
                                key={skill}
                                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#005A70]/10 text-[#005A70] dark:text-teal-400 border border-[#005A70]/15"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}

                        <a
                          href={`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(job.role)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 mt-3 text-xs font-medium text-[#005A70] dark:text-teal-400 hover:underline"
                        >
                          <ExternalLink size={12} /> View on LinkedIn
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-6">
                    No job openings found. Try adjusting your skills or target role.
                  </p>
                )}
              </Card>
            )}

            {/* Roadmap view */}
            {step3View === 'roadmap' && roadmap && (
              <Card title="12-Week Career Roadmap" subtitle={`Tailored for ${targetRole}`}>
                {roadmap.weeks?.length ? (
                  <div className="space-y-3">
                    {roadmap.weeks.map((week) => (
                      <div key={week.week} className="flex gap-3 p-3 rounded-xl border border-slate-100 dark:border-slate-700/60 hover:border-[#005A70]/30 transition-colors">
                        <div className="w-10 h-10 rounded-xl bg-[#005A70]/10 flex items-center justify-center text-[#005A70] dark:text-teal-400 font-bold text-xs shrink-0">
                          W{week.week}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{week.title}</p>
                          <ul className="mt-1 space-y-0.5">
                            {week.tasks.slice(0, 3).map((t, i) => (
                              <li key={i} className="text-xs text-slate-500 dark:text-slate-400 flex items-start gap-1.5">
                                <span className="mt-0.5 w-1 h-1 rounded-full bg-[#005A70]/50 shrink-0" />
                                {t}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : roadmap.roadmap ? (
                  renderRoadmap(roadmap.roadmap)
                ) : (
                  <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-6">
                    No roadmap data available.
                  </p>
                )}
              </Card>
            )}

            <Button
              variant="secondary"
              icon={<ArrowLeft size={16} />}
              onClick={() => setStep(2)}
              className="w-full rounded-xl"
            >
              Back to Skills
            </Button>
          </div>
        )}
      </div>

      {/* RIGHT PANEL: UNIFIED AI CHAT */}
      <ChatPanel
        initialMessage="Hi! I'm NexusAI, your career co-pilot. Ask me about jobs, skills, roadmaps, government schemes (PMKVY, SWAYAM), interview tips, or anything career-related. You can also upload your resume on the left to get a personalized plan."
        className="col-span-3"
      />
    </div>
  )
}
