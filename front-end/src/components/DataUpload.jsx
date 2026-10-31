// DataUpload.jsx
// Thanh công cụ nạp dữ liệu đầu vào: văn bản pháp luật, hồ sơ ứng viên
// (tải file hoặc thư mục) và nút xét hồ sơ để chạy toàn bộ pipeline.
import { useState } from "react";
import Icon from "./Icon.jsx";

export default function DataUpload({
  lawInput,
  candidateFileInput,
  candidateFolderInput,
  onLawUpload,
  onCandidateUpload,
  onEvaluate,
  isLoading,
  lawFiles,
  onClearLawFiles,
}) {
  // Trạng thái mở/đóng menu chọn cách thêm hồ sơ (file hoặc thư mục).
  const [showCandidateMenu, setShowCandidateMenu] = useState(false);

  // Mở hộp chọn file hồ sơ và đóng menu.
  function chooseCandidateFile() {
    candidateFileInput.current?.click();
    setShowCandidateMenu(false);
  }

  // Mở hộp chọn thư mục hồ sơ và đóng menu.
  function chooseCandidateFolder() {
    candidateFolderInput.current?.click();
    setShowCandidateMenu(false);
  }

  return <>
    {/* Thanh nút bấm và các input file ẩn */}
    <div className="upload-toolbar">
      <div className="upload-toolbar-title"><Icon>▣</Icon>
        <div>
          <strong>Nguồn dữ liệu</strong>
        </div>
      </div>

      <div className="upload-actions">
        {/* Nút 1: thêm văn bản pháp luật */}
        <button className="button button-outline" onClick={() => lawInput.current?.click()}>
          <Icon>＋</Icon> Thêm văn bản luật
        </button>

        {/* Nút 2: thêm hồ sơ - mở menu chọn tải file hoặc thư mục */}
        <div className="upload-button-group">
          <button
            className="button button-outline"
            onClick={() => setShowCandidateMenu(open => !open)}
            disabled={isLoading}
            aria-haspopup="menu"
            aria-expanded={showCandidateMenu}
          >
            <Icon>＋</Icon> Thêm hồ sơ
          </button>
          {showCandidateMenu && <div className="upload-menu" role="menu">
            <button type="button" role="menuitem" onClick={chooseCandidateFile}>Tải file hồ sơ</button>
            <button type="button" role="menuitem" onClick={chooseCandidateFolder}>Tải thư mục hồ sơ</button>
          </div>}
        </div>

        {/* Nút 3: xét hồ sơ - gọi pipeline (tạm thời in dữ liệu ra console) */}
        <button className="button button-primary" onClick={onEvaluate} disabled={isLoading}>
          <Icon>✓</Icon> Xét hồ sơ
        </button>
      </div>

      {/* Input ẩn: văn bản luật, hồ sơ dạng file và hồ sơ dạng thư mục */}
      <input ref={lawInput} type="file" accept=".pdf,.doc,.docx,.txt,.json" multiple hidden onChange={onLawUpload} />
      <input ref={candidateFileInput} type="file" accept=".json,application/json,.txt" multiple hidden onChange={onCandidateUpload} />
      <input ref={candidateFolderInput} type="file" accept=".json,application/json,.txt" multiple hidden onChange={onCandidateUpload} {...{ webkitdirectory: "", directory: "" }} />
    </div>

    {/* Danh sách tài liệu pháp luật đã thêm (chỉ hiển thị khi có dữ liệu) */}
    {lawFiles.length > 0 && <div className="law-files">
      <div className="law-files-heading">
        <strong><Icon>▧</Icon> Văn bản đã thêm ({lawFiles.length})</strong>
        <button className="text-button" onClick={onClearLawFiles}>Xóa danh sách</button>
      </div>

      <div className="file-chips">{lawFiles.map((file, index) =>
        <span className="file-chip" key={`${file.name}-${index}`}>
          <Icon>▤</Icon> {file.name}
        </span>)}
      </div>
    </div>}
  </>;
}
