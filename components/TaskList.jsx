export default function TaskList({tasks=[]}){
  return (
    <div>
      {tasks.length===0 ? (
        <div>No tasks yet — this is a placeholder UI to connect to the API later.</div>
      ) : (
        <ul>
          {tasks.map(t => (
            <li key={t.id}>{t.title} — {t.clientName || 'No client'}</li>
          ))}
        </ul>
      )}
    </div>
  )
}