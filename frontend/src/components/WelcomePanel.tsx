import { ArrowUpRight, Code2, FileText, Lightbulb, Sparkles, Orbit } from "lucide-react";

const suggestions = [
  { icon: Lightbulb, title: "Explore an idea", description: "Turn a spark into something real", prompt: "Help me brainstorm a creative project idea and turn it into a practical plan.", color: "mint" },
  { icon: Code2, title: "Build something", description: "Your next project starts here", prompt: "Help me plan and build a project. Start by asking what I want to create.", color: "blue" },
  { icon: FileText, title: "Make it simple", description: "Find clarity in the complex", prompt: "Help me understand a complex topic. Ask me which topic I want to explore.", color: "purple" },
];

export default function WelcomePanel({ onSuggest }: { onSuggest: (text: string) => void }) {
  return <section className="welcome-panel">
    <div className="welcome-label"><span /> A SPACE FOR YOUR NEXT BIG IDEA</div>
    <div className="intelligence-orb" aria-hidden="true"><div className="orb-ring ring-one" /><div className="orb-ring ring-two" /><div className="orb-core"><Orbit size={42} strokeWidth={1} /></div><i className="orb-satellite" /></div>
    <h2>A little curiosity.<br /><span>Infinite possibilities.</span></h2>
    <p className="welcome-description">Your thoughts, with a little more possibility.<br />Think, create, and figure things out together.</p>
    <div className="language-note"><Sparkles size={13} /> English, Tamil, or a little of both.</div>
    <div className="suggestion-grid">{suggestions.map(({ icon: Icon, ...item }, index) => <button key={item.title} onClick={() => onSuggest(item.prompt)} className={`suggestion-card ${item.color}`}>
      <div className="suggestion-top"><span className="suggestion-icon"><Icon size={18} /></span><span className="suggestion-number">0{index + 1}</span></div>
      <strong>{item.title}<ArrowUpRight size={16} /></strong><p>{item.description}</p>
    </button>)}</div>
  </section>;
}
