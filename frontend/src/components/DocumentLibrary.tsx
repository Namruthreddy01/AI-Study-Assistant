import { useState } from "react";
import {
  BrainCircuit,
  CheckSquare,
  FileText,
  FileUp,
  Layers,
  Sparkles,
  Square,
  Trash2
} from "lucide-react";
import { DocumentUploader } from "./DocumentUploader";
import type { DocumentItem } from "../types";

type Props = {
  documents: DocumentItem[];
  selectedDocIds: string[];
  busy: boolean;
  onToggleDoc: (docId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onUpload: (file: File) => Promise<void>;
  onDeleteDoc: (docId: string) => Promise<void>;
  onStudySelected: () => void;
};

export function DocumentLibrary({
  documents,
  selectedDocIds,
  busy,
  onToggleDoc,
  onSelectAll,
  onDeselectAll,
  onUpload,
  onDeleteDoc,
  onStudySelected
}: Props) {
  const [docToDelete, setDocToDelete] = useState<DocumentItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  const confirmDelete = async () => {
    if (!docToDelete) return;
    setDeleting(true);
    try {
      await onDeleteDoc(docToDelete.id);
      setDocToDelete(null);
    } finally {
      setDeleting(false);
    }
  };

  const allSelected = documents.length > 0 && selectedDocIds.length === documents.length;

  return (
    <section className="document-library">
      <div className="library-header-actions">
        <div className="selection-stats">
          <span className="selection-pill">
            <strong>{selectedDocIds.length}</strong> of <strong>{documents.length}</strong> material{documents.length === 1 ? "" : "s"} selected
          </span>
          <div className="selection-buttons">
            <button
              type="button"
              className="action-link-btn"
              disabled={busy || documents.length === 0}
              onClick={allSelected ? onDeselectAll : onSelectAll}
            >
              {allSelected ? <Square size={15} /> : <CheckSquare size={15} />}
              {allSelected ? "Deselect All" : "Select All"}
            </button>
          </div>
        </div>

        {selectedDocIds.length > 0 && (
          <button
            type="button"
            className="primary-button"
            disabled={busy}
            onClick={onStudySelected}
          >
            <BrainCircuit size={16} />
            Ask AI Across Selected ({selectedDocIds.length})
          </button>
        )}
      </div>

      <DocumentUploader busy={busy} onUpload={onUpload} />

      {!documents.length ? (
        <div className="empty-state">
          <FileText size={38} />
          <p>No study materials uploaded yet. Drop a PDF above to get started!</p>
        </div>
      ) : (
        <div className="library-grid">
          {documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            const uploadDate = new Date(doc.created_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric"
            });

            return (
              <article
                key={doc.id}
                className={`library-doc-card ${isSelected ? "selected" : ""}`}
                onClick={() => onToggleDoc(doc.id)}
              >
                <div className="card-top-row">
                  <div className="checkbox-indicator">
                    {isSelected ? (
                      <CheckSquare size={19} className="check-icon active" />
                    ) : (
                      <Square size={19} className="check-icon" />
                    )}
                  </div>
                  <span className="status-badge">
                    <span className="status-dot" /> {doc.status}
                  </span>
                  <button
                    type="button"
                    className="delete-doc-btn"
                    title="Delete document"
                    disabled={busy}
                    onClick={(e) => {
                      e.stopPropagation();
                      setDocToDelete(doc);
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <div className="card-doc-info">
                  <div className="doc-type-icon">
                    <FileText size={20} />
                  </div>
                  <h3 title={doc.filename}>{doc.filename}</h3>
                </div>

                <div className="card-meta-grid">
                  <div>
                    <dt>Pages</dt>
                    <dd>{doc.pages}</dd>
                  </div>
                  <div>
                    <dt>Chunks</dt>
                    <dd>{doc.chunks}</dd>
                  </div>
                  {doc.flashcard_count !== undefined && (
                    <div>
                      <dt>Flashcards</dt>
                      <dd>{doc.flashcard_count}</dd>
                    </div>
                  )}
                </div>

                <div className="card-date-footer">
                  <span>Uploaded {uploadDate}</span>
                  {isSelected && <span className="active-tag">Active in Study</span>}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {docToDelete && (
        <div className="modal-backdrop" onClick={() => !deleting && setDocToDelete(null)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Delete Study Material?</h3>
            <p>
              Are you sure you want to delete <strong>{docToDelete.filename}</strong>?
            </p>
            <p className="modal-warning">
              This will permanently remove the uploaded PDF, chunk indexes, FAISS vector embeddings, and any associated flashcards.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="secondary-button"
                disabled={deleting}
                onClick={() => setDocToDelete(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="danger-button"
                disabled={deleting}
                onClick={() => void confirmDelete()}
              >
                {deleting ? "Deleting…" : "Delete Permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
