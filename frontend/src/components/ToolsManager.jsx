import React, { useState, useEffect } from 'react';
import { Settings, Search, Copy, Check, AlertCircle, Sparkles } from 'lucide-react';
import axios from 'axios';
import AddConnectionModal from './AddConnectionModal'
import useStore from '../store/useStore'

export default function ToolsManager() {
  const { connections, setConnections, notify } = useStore()
  const [department, setDepartment] = useState('sales');
  const [departments, setDepartments] = useState([]);
  const [tools, setTools] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [promptQuery, setPromptQuery] = useState('');
  const [selectedTool, setSelectedTool] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [launchApp, setLaunchApp] = useState(null)

  useEffect(() => {
    loadDepartments();
  }, []);

  useEffect(() => {
    loadToolsForDepartment(department);
  }, [department]);

  const loadDepartments = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/auto-config/supported-departments'
      );
      setDepartments(response.data.supported_departments);
    } catch (err) {
      console.error('Failed to load departments:', err);
    }
  };

  const loadToolsForDepartment = async (dept) => {
    setIsLoading(true);
    try {
      const response = await axios.get(
        `http://localhost:8000/api/tools/department/${dept}`
      );
      setTools(response.data.tools);
      setSelectedTool(null);
    } catch (err) {
      console.error('Failed to load tools:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const searchTools = async () => {
    if (!searchQuery.trim()) {
      loadToolsForDepartment(department);
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.get(
        'http://localhost:8000/api/tools/search',
        { params: { query: searchQuery, department } }
      );
      setTools(response.data.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const findToolFromPrompt = async () => {
    const prompt = promptQuery.trim()
    if (!prompt) return

    const lower = prompt.toLowerCase()
    if (
      lower.includes('resume') ||
      lower.includes('cv') ||
      lower.includes('candidate') ||
      lower.includes('screen applicant') ||
      lower.includes('summarize resume')
    ) {
      setDepartment('hr')
      try {
        const response = await axios.get('http://localhost:8000/api/tools/department/hr')
        setTools(response.data.tools)
        const tool = response.data.tools.resume_screener
        if (tool) {
          setSelectedTool({ name: 'resume_screener', ...tool })
          notify('Resume Screener found from your prompt', 'success')
        }
      } catch (err) {
        console.error('Failed to load HR tools:', err)
      }
      return
    }

    setIsLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/tools/search', {
        params: { query: prompt, department },
      })
      setTools(response.data.results)
      const firstMatch = Object.entries(response.data.results || {})[0]
      if (firstMatch) {
        setSelectedTool({ name: firstMatch[0], ...firstMatch[1] })
        notify(`Matched tool "${firstMatch[0]}" from your prompt`, 'success')
      } else {
        notify('No matching tool found for that prompt', 'info')
      }
    } catch (err) {
      console.error('Prompt search failed:', err)
      notify('Prompt search failed', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredTools = Object.entries(tools).map(([name, info]) => ({
    name,
    ...info
  }));

  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-8 text-gray-900 flex items-center gap-2">
        <Settings className="w-8 h-8 text-indigo-600" />
        Tools Manager
      </h2>

      {/* Department & Search */}
      <div className="mb-8 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Find Extension By Prompt
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={promptQuery}
              onChange={(e) => setPromptQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && findToolFromPrompt()}
              placeholder='Example: screen this resume and give me a summary'
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              onClick={findToolFromPrompt}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Find
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept.charAt(0).toUpperCase() + dept.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Tools
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchTools()}
                placeholder="Search by name or description..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <button
                onClick={searchTools}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tools List */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Available Tools ({filteredTools.length})
          </h3>
          <div className="space-y-2">
            {isLoading ? (
              <div className="text-center py-8 text-gray-500">Loading tools...</div>
            ) : filteredTools.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No tools found</div>
            ) : (
              filteredTools.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => setSelectedTool(tool)}
                  className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all ${
                    selectedTool?.name === tool.name
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {tool.name}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Tool Details */}
        <div className="lg:col-span-2">
          {selectedTool ? (
            <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                {selectedTool.name}
              </h3>

              <div className="space-y-6">
                {/* Description */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Description</p>
                  <p className="text-gray-600">{selectedTool.description}</p>
                </div>

                {/* Parameters */}
                {selectedTool.params && selectedTool.params.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-3">Parameters</p>
                    <div className="space-y-2">
                      {selectedTool.params.map((param) => (
                        <div
                          key={param}
                          className="p-3 bg-white border border-gray-300 rounded flex items-center justify-between"
                        >
                          <span className="font-mono text-sm text-gray-700">{param}</span>
                          <button
                            onClick={() => copyToClipboard(param, param)}
                            className="text-gray-400 hover:text-gray-600 transition-all"
                          >
                            {copiedId === param ? (
                              <Check className="w-4 h-4 text-green-600" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Return Values */}
                {selectedTool.returns && selectedTool.returns.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-3">Returns</p>
                    <div className="space-y-2">
                      {selectedTool.returns.map((ret) => (
                        <div
                          key={ret}
                          className="p-3 bg-white border border-gray-300 rounded flex items-center justify-between"
                        >
                          <span className="font-mono text-sm text-gray-700">{ret}</span>
                          <button
                            onClick={() => copyToClipboard(ret, ret)}
                            className="text-gray-400 hover:text-gray-600 transition-all"
                          >
                            {copiedId === ret ? (
                              <Check className="w-4 h-4 text-green-600" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Usage Example */}
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-900 mb-1">How to use</p>
                    <p className="text-sm text-blue-800">
                      This tool can be automatically configured and sequenced with other tools based on your task requirements. Use the Auto-Configurator to build complete agent workflows.
                    </p>
                  </div>
                </div>

                {selectedTool.name === 'resume_screener' && (
                  <button
                    onClick={async () => {
                      try {
                        const app = await axios.get('http://localhost:8000/api/connections/apps/resume_screener')
                        setLaunchApp(app.data)
                      } catch (err) {
                        notify('Failed to open Resume Screener', 'error')
                      }
                    }}
                    className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all"
                  >
                    Open Resume Screener
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>Select a tool to view details</p>
            </div>
          )}
        </div>
      </div>

      {launchApp && (
        <AddConnectionModal
          app={launchApp}
          onClose={() => setLaunchApp(null)}
          onAdded={(newConn) => setConnections([...connections, newConn])}
        />
      )}
    </div>
  );
}
