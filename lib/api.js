const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export async function fetchTasks(){
  const res = await fetch(API_BASE + '/tasks')
  if(!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

export async function fetchClient(id){
  const res = await fetch(API_BASE + '/clients/' + id)
  return res.json()
}

export default { fetchTasks, fetchClient }