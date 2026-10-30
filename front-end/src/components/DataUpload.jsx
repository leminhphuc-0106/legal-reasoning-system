// DataUpload.jsx
// Thanh công cụ nạp dữ liệu đầu vào: file tiêu chí (JSON), văn bản pháp luật
// (nhiều định dạng) và hồ sơ ứng viên (JSON, có thể chọn cả thư mục).
import Icon from "./Icon.jsx";

export default function DataUpload({ criteriaInput, lawInput, candidateInput, 
  onCriteriaUpload, onLawUpload, onCandidateUpload, 
  isLoading, lawFiles, onClearLawFiles }) {

  return <>
    {/* Thanh nút bấm và các input file ẩn */}
    <div className="upload-toolbar">
      <div className="upload-toolbar-title"><Icon>▣</Icon>
        <div>
          <strong>Nguồn dữ liệu</strong>
          {/* <span>Quản lý văn bản và hồ sơ đầu vào</span> */}
        </div>
      </div>


      <div className="upload-actions">
        {/* Mỗi nút mở hộp chọn tệp tương ứng thông qua ref */}
        {/* .current là một thuộc tính của React Ref (useRef) */}

        <button className="button button-outline" onClick={() => lawInput.current?.click()}>
          <Icon>＋</Icon> Thêm văn bản luật
        </button>

        <button className="button button-primary" onClick={() => candidateInput.current?.click()} disabled={isLoading}>
          <Icon>＋</Icon> Thêm hồ sơ
        </button>

      </div>

      
      {/* Input ẩn: tiêu chí JSON, văn bản luật, và hồ sơ (chọn được nhiều file/thư mục) */}
      <input ref={lawInput} type="file" accept=".pdf,.doc,.docx,.txt,.json" multiple hidden onChange={onLawUpload} />
      <input ref={candidateInput} type="file" accept=".json,application/json, .txt" 
      multiple hidden onChange={onCandidateUpload} {...{ webkitdirectory: "", directory: "" }} />

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
