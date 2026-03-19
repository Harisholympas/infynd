import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, Download, Search, Plus, CheckCircle } from 'lucide-react';
import { knowledgeBaseAPI } from '../utils/api'

export default function KnowledgeBaseManager() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDesc, setNewKBDesc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [fileUploading, setFileUploading] = useState(false);

  const companyId = 'default'; // Would come from auth context

  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    setIsLoading(true);
    try {
      const response = await knowledgeBaseAPI.list(companyId)
      setKnowledgeBases(response.knowledge_bases || []);
    } catch (err) {
      setError('Failed to load knowledge bases');
    } finally {
      setIsLoading(false);
    }
  };

  const createNewKB = async () => {
    if (!newKBName.trim()) {
      setError('Please enter a knowledge base name');
      return;
    }

    setIsLoading(true);
    try {
      const response = await knowledgeBaseAPI.create({
        name: newKBName,
        description: newKBDesc,
        company_id: companyId,
      })

      // Reload for canonical list + counts
      await loadKnowledgeBases()
      setNewKBName('');
      setNewKBDesc('');
      setSuccess(response.message || 'Knowledge base created successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to create knowledge base');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e, kbId) => {
    const files = e.target.files;
    if (!files) return;

    setFileUploading(true);
    try {
      for (let file of files) {
        await knowledgeBaseAPI.uploadDocument(kbId, file)
      }

      setSuccess(`${files.length} file(s) uploaded successfully`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to upload files');
    } finally {
      setFileUploading(false);
    }
  };

  const deleteKB = async (kbId) => {
    if (window.confirm('Are you sure? This will delete all documents in this knowledge base.')) {
      try {
        await knowledgeBaseAPI.delete(kbId)
        setKnowledgeBases(knowledgeBases.filter(kb => kb.id !== kbId));
        setSelectedKB(null);
        setSuccess('Knowledge base deleted');
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        setError('Failed to delete knowledge base');
      }
    }
  };

  const searchKB = async () => {
    if (!selectedKB || !searchQuery.trim()) return;

    setIsLoading(true);
    try {
      const response = await knowledgeBaseAPI.search(selectedKB.id, searchQuery, 5)

      // Show search results
      alert(`Found ${(response.results || []).length} relevant documents`);
    } catch (err) {
      setError('Search failed');
    } finally {
      setIsLoading(false);
    }
  };

  const exportKB = async (kbId) => {
    try {
      const response = await knowledgeBaseAPI.export(kbId)
      
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `kb-${kbId}.json`;
      link.click();
    } catch (err) {
      setError('Failed to export knowledge base');
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-8 text-gray-900">Knowledge Base Manager</h2>

      {/* Create New KB */}
      <div className="mb-8 p-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Knowledge Base</h3>
        <div className="space-y-4">
          <input
            type="text"
            value={newKBName}
            onChange={(e) => setNewKBName(e.target.value)}
            placeholder="Knowledge base name (e.g., HR Policies, Sales Process)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <textarea
            value={newKBDesc}
            onChange={(e) => setNewKBDesc(e.target.value)}
            placeholder="Description (optional)"
            rows="2"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            onClick={createNewKB}
            disabled={isLoading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition-all flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Knowledge Base
          </button>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          {success}
        </div>
      )}

      {/* Knowledge Bases Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {knowledgeBases.map((kb) => (
          <div
            key={kb.id}
            onClick={() => setSelectedKB(kb)}
            className={`p-6 rounded-lg border-2 cursor-pointer transition-all ${
              selectedKB?.id === kb.id
                ? 'border-indigo-600 bg-indigo-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <h4 className="font-semibold text-gray-900 mb-2">{kb.name}</h4>
            <p className="text-sm text-gray-600 mb-4">{kb.description}</p>
            <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {kb.document_count || 0} documents
              </span>
              <span>{new Date(kb.created_at).toLocaleDateString()}</span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteKB(kb.id);
                }}
                className="px-3 py-1 text-red-600 hover:bg-red-50 rounded transition-all flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  exportKB(kb.id);
                }}
                className="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded transition-all flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Selected KB Details */}
      {selectedKB && (
        <div className="p-6 bg-gray-50 rounded-lg">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            {selectedKB.name} - Upload Documents
          </h3>

          {/* File Upload */}
          <div className="mb-6 p-4 border-2 border-dashed border-gray-300 rounded-lg">
            <label className="flex items-center justify-center cursor-pointer">
              <div className="text-center">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600 font-medium">
                  {fileUploading ? 'Uploading...' : 'Click to upload documents (PDF, TXT, JSON)'}
                </p>
              </div>
              <input
                type="file"
                multiple
                onChange={(e) => handleFileUpload(e, selectedKB.id)}
                disabled={fileUploading}
                className="hidden"
                accept=".pdf,.txt,.json,.doc,.docx"
              />
            </label>
          </div>

          {/* Search Knowledge Base */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Search Knowledge Base</h4>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <button
                onClick={searchKB}
                disabled={isLoading || !searchQuery.trim()}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition-all flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
                Search
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading && knowledgeBases.length === 0 && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin">
            <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full"></div>
          </div>
          <p className="mt-4 text-gray-600">Loading knowledge bases...</p>
        </div>
      )}
    </div>
  );
}
