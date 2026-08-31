import { ChangeEvent, useRef, useState } from "react";
import { FileUp, LoaderCircle, Sparkles } from "lucide-react";

type Props = {
  busy: boolean;
  onUpload: (file: File) => Promise<void>;
};

export function DocumentUploader({ busy, onUpload }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pick = async (files: FileList | null) => {
    const file = files?.[0];
    if (file) await onUpload(file);
  };

  return (
    <section
      className={"upload-card " + (dragging ? "dragging" : "")}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        void pick(event.dataTransfer.files);
      }}
    >
      <div className="upload-icon"><FileUp size={25} /></div>
      <div>
        <h2>Bring your notes to life</h2>
        <p>Drop a PDF here and turn it into answers, quizzes, and revision material.</p>
      </div>
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(event: ChangeEvent<HTMLInputElement>) => void pick(event.target.files)}
      />
      <button className="primary-button" disabled={busy} onClick={() => input.current?.click()}>
        {busy ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}
        {busy ? "Processing PDF…" : "Upload material"}
      </button>
      <small>PDF only · up to 20 MB · selectable text required</small>
    </section>
  );
}

