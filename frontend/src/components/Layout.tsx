import React from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import './Layout.css'

export default function Layout() {
  const { teacher, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1 className="logo">PhysicsPulse</h1>
          <p className="teacher-name">{teacher?.full_name || teacher?.email}</p>
        </div>
        <ul className="nav-links">
          <li><NavLink to="/" end>Dashboard</NavLink></li>
          <li><NavLink to="/videos">Videos</NavLink></li>
          <li><NavLink to="/sessions">Sessions</NavLink></li>
        </ul>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
