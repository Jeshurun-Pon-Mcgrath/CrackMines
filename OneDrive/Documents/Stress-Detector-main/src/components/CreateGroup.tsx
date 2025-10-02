'use client'

import { useState } from 'react'
import { useSession } from 'next-auth/react'
import io from 'socket.io-client'

interface CreateGroupProps {
  onClose: () => void
  onGroupCreated?: (details: { groupName: string; inviteCode: string; inviteLink: string }) => void
}

export default function CreateGroup({ onClose, onGroupCreated }: CreateGroupProps) {
  const { data: session } = useSession()
  const [groupName, setGroupName] = useState('')
  const [description, setDescription] = useState('')
  const [groupType, setGroupType] = useState<'public' | 'private'>('public')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!groupName.trim() || !session?.user?.email) return

    setLoading(true)
    
    // Create group via socket
    const socket = io('http://localhost:3002')
    
    // Listen for group creation details (for private groups)
    socket.on('group-created-details', (groupDetails) => {
      if (groupDetails.type === 'private' && onGroupCreated) {
        onGroupCreated({
          groupName: groupDetails.name,
          inviteCode: groupDetails.inviteCode,
          inviteLink: groupDetails.inviteLink
        })
      }
      setLoading(false)
      onClose()
      socket.disconnect()
    })
    
    // Listen for errors
    socket.on('error', (error) => {
      console.error('Group creation error:', error)
      alert(`Error creating group: ${error}`)
      setLoading(false)
      socket.disconnect()
    })
    
    const groupData = {
      name: groupName,
      description: description,
      type: groupType,
      createdBy: session.user.email // Add the user email as creator
    }
    
    console.log('Sending group data:', groupData)
    socket.emit('create-group', groupData)
    
    // Fallback timeout for public groups
    setTimeout(() => {
      if (groupType === 'public') {
        setLoading(false)
        onClose()
        socket.disconnect()
      }
    }, 1000)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Create New Group
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition duration-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="groupName" className="block text-sm font-medium text-gray-700 mb-2">
                Group Name *
              </label>
              <input
                type="text"
                id="groupName"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="Enter group name"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this group is about"
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Group Type
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="groupType"
                    value="public"
                    checked={groupType === 'public'}
                    onChange={(e) => setGroupType(e.target.value as 'public' | 'private')}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    🌍 <strong>Public</strong> - Anyone can join this group
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="groupType"
                    value="private"
                    checked={groupType === 'private'}
                    onChange={(e) => setGroupType(e.target.value as 'public' | 'private')}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    🔒 <strong>Private</strong> - Invite-only group with code and link
                  </span>
                </label>
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!groupName.trim() || loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-lg transition duration-200"
              >
                {loading ? 'Creating...' : 'Create Group'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}