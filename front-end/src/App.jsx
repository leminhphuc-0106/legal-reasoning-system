// App.jsx
// Thành phần gốc của ứng dụng: quản lý toàn bộ trạng thái (tiêu chí, hồ sơ,
// hội thoại, tài liệu) và điều phối các component con trong màn hình đánh giá.
import { useMemo, useRef, useState } from "react";
import MainLayout from "./layouts/MainLayout.jsx";
import DataUpload from "./components/DataUpload.jsx";
import CandidateOverview from "./components/CandidateOverview.jsx";
import SummaryCard from "./components/SummaryCard.jsx";
import CriteriaList from "./components/CriteriaList.jsx";
import Icon from "./components/Icon.jsx";
import { initialCriteria, initialCandidates } from "./data/initialData.js";
import { normalizeCandidate, readJsonFile } from "./utils/normalize.js";
import { askAssistant } from "./services/chatService.js";
import "./App.css";

// Tin nhắn chào mừng mặc định của trợ lý khi mở ứng dụng.
const welcomeMessage = "Xin chào! Tôi có thể hỗ trợ tra cứu quy định, đối chiếu tiêu chí và tổng hợp thông tin hồ sơ ứng viên. Hãy chọn một ứng viên ở bên phải hoặc nhập câu hỏi bên dưới.";

export default function App() {
  // Các ref trỏ tới input file ẩn, dùng để mở hộp chọn tệp từ nút bấm.
  // => DÙNG ĐỂ TẢI CÁC FILE LÊN
  // Tách riêng input chọn file và input chọn thư mục cho hồ sơ.
  const lawInput = useRef(null);
  const candidateFileInput = useRef(null);
  const candidateFolderInput = useRef(null);


  // Trạng thái dữ liệu chính của ứng dụng.
  // Khi có Backend, những thông tin này sẽ được lấy thông qua hoạt động của chatbot AI
  const [criteria, setCriteria] = useState(initialCriteria);
  const [candidates, setCandidates] = useState(initialCandidates);



  // Hồ sơ đang được chọn và bộ lọc trạng thái tiêu chí (all/pass/fail/pending).
  const [selectedId, setSelectedId] = useState("HS001");
  const [filter, setFilter] = useState("all");

  // Nội dung câu hỏi đang nhập và lịch sử hội thoại với trợ lý.
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([{ role: "assistant", content: welcomeMessage }]);


  // Danh sách tài liệu pháp luật đã thêm và thông báo trạng thái gần nhất.
  const [lawFiles, setLawFiles] = useState([]);
  const [notice, setNotice] = useState("");


  // Cờ báo đang xử lý khi đọc/khôi phục hồ sơ.
  const [isLoading, setIsLoading] = useState(false);

  // Hồ sơ hiện tại được chọn; nếu không tìm thấy thì lấy hồ sơ đầu tiên.
  const selectedCandidate = candidates.find(item => item.id === selectedId) ?? candidates[0];


  // Ghép tiêu chí với kết quả đối chiếu của hồ sơ đang chọn để hiển thị.
  const results = useMemo(() => {

    if (!selectedCandidate) return [];

    return criteria.map(criterion => {
      const result = selectedCandidate.criteriaResults.find(item => item.criterionId === criterion.id);
      
      return { ...criterion, status: result?.status ?? "pending", reason: result?.reason 
        || "Chưa có kết quả đối chiếu cho tiêu chí này.", evidence: result?.evidence 
        || "Chưa có minh chứng được ghi nhận." };
    });

  }, [criteria, selectedCandidate]);


  // Thống kê số tiêu chí theo từng trạng thái và tỷ lệ đạt tổng thể.
  const counts = {
    pass: results.filter(item => item.status === "pass").length,
    fail: results.filter(item => item.status === "fail").length,
    pending: results.filter(item => item.status === "pending").length,
  };

  const percentage = results.length ? Math.round(counts.pass / results.length * 100) : 0;
  // Danh sách tiêu chí sau khi áp dụng bộ lọc hiện tại.
  const visibleResults = results.filter(item => filter === "all" || item.status === filter);


  // Ghi nhận danh sách tài liệu pháp luật (chỉ lưu thông tin tệp để hiển thị).
  function handleLawUpload(event) {
    const files = Array.from(event.target.files ?? []);
   
   
    if (!files.length) return;
    setLawFiles(previous => [...previous, ...files.map(file => ({ name: file.name, size: file.size, type: file.type 
      || "Không xác định" }))]);
    
    
    setNotice(`Đã thêm ${files.length} tài liệu pháp luật vào danh sách.`);

    event.target.value = "";
  }

  // Đọc một hoặc nhiều file JSON hồ sơ, chuẩn hóa và gộp vào danh sách ứng viên.
  async function handleCandidateUpload(event) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;
    setIsLoading(true);
    try {
      const jsonFiles = files.filter(file => file.name.toLowerCase().endsWith(".json"));
      if (!jsonFiles.length) throw new Error("Vui lòng chọn ít nhất một file JSON hồ sơ.");
      const parsed = await Promise.all(jsonFiles.map(async file => ({ fileName: file.name, data: await readJsonFile(file) })));
      const loaded = [];
      parsed.forEach(({ fileName, data }) => {
        const items = Array.isArray(data) 
        ? data : Array.isArray(data?.candidates) 
        ? data.candidates : Array.isArray(data?.ung_vien) 
        ? data.ung_vien : [data];
        items.forEach(item => {
          const candidate = normalizeCandidate(item, loaded.length);
          const uniqueId = candidate.id && !loaded.some(c => c.id === candidate.id) 
          ? candidate.id : `${candidate.id}-${loaded.length + 1}`;
          loaded.push({ ...candidate, id: uniqueId, sourceFile: fileName });
        });
      });
      if (!loaded.length) throw new Error("Không tìm thấy hồ sơ hợp lệ.");
      setCandidates(previous => {
        const byId = new Map(previous.map(item => [item.id, item]));
        loaded.forEach(item => byId.set(item.id, item));
        return Array.from(byId.values());
      });
      setSelectedId(loaded[0].id); setFilter("all");
      setNotice(`Đã đọc ${loaded.length} hồ sơ từ ${jsonFiles.length} file JSON.`);
    } catch (error) { setNotice(`Không đọc được hồ sơ: ${error.message}`); }
    finally { setIsLoading(false); event.target.value = ""; }
  }

  // Xét hồ sơ: nơi sẽ gọi API chạy toàn bộ pipeline xử lý.
  // Hiện backend chưa có nên tạm thời in dữ liệu đầu vào ra console.
  function handleEvaluate() {
    const payload = {
      lawFiles: lawFiles.map(file => file.name),
      candidates: candidates.map(candidate => candidate.id),
      criteria: criteria.map(criterion => criterion.id),
    };
    console.log("Xét hồ sơ - dữ liệu pipeline:", payload);
    setNotice("Đã gửi yêu cầu xét hồ sơ (API pipeline chưa được kết nối).");
  }

  // Gửi câu hỏi của người dùng tới trợ lý và thêm câu trả lời vào hội thoại.
  async function sendMessage(event) {
    event.preventDefault();
    const content = query.trim();
    if (!content) return;
    setMessages(previous => [...previous, { role: "user", content }]);
    setQuery("");
    try {
      const answer = await askAssistant(content);
      setMessages(previous => [...previous, { role: "assistant", content: answer }]);
    } catch {
      setMessages(previous => [...previous, { role: "assistant", content: "Không thể kết nối backend lúc này." }]);
    }
  }

  // Khôi phục toàn bộ dữ liệu minh họa và trạng thái ban đầu.
  function resetApp() {
    setCriteria(initialCriteria); setCandidates(initialCandidates); setSelectedId("HS001");
    setFilter("all"); setLawFiles([]); setNotice("Đã khôi phục dữ liệu minh họa ban đầu.");
    setMessages([{ role: "assistant", content: welcomeMessage }]); setQuery("");
  }

  // Bố cục gồm khung chung (MainLayout) và vùng kết quả đánh giá bên phải.
  return <MainLayout onReset={resetApp} chatProps={{ messages, notice, query, setQuery, onSend: sendMessage }}>
    
    {/* Tiêu đề khu vực kết quả và nút xuất báo cáo (in ra PDF) */}
    <div className="results-heading">
      <div className="title-results-heading">
        <h2>
          {/* <Icon>▤</Icon>  */}
          Kết quả đối chiếu hồ sơ
        </h2>
        {/* <p className="section-subtitle">Tổng hợp tiêu chí và minh chứng theo dữ liệu đã cung cấp</p> */}
      </div>
      <button className="button button-secondary export-button" onClick={() => window.print()}>
        <Icon>⇩</Icon> Xuất báo cáo
      </button>

    </div>


    {/* Khu vực nạp dữ liệu: tiêu chí, văn bản luật và hồ sơ ứng viên */}
    <DataUpload 
    lawInput={lawInput} 
    candidateFileInput={candidateFileInput} 
    candidateFolderInput={candidateFolderInput} 
    onLawUpload={handleLawUpload} 
    onCandidateUpload={handleCandidateUpload} 
    onEvaluate={handleEvaluate}
    isLoading={isLoading} 
    lawFiles={lawFiles} 
    onClearLawFiles={() => setLawFiles([])} />

    
    {/* Thanh chọn hồ sơ đang xem */}
    <div className="candidate-toolbar"><label htmlFor="candidate-select"><Icon>♙</Icon> Hồ sơ đang xem</label>
      <select id="candidate-select" 
      value={selectedCandidate?.id ?? ""} 
      onChange={event => { setSelectedId(event.target.value); setFilter("all"); }}>

        {candidates.map(candidate => 
          <option key={candidate.id} value={candidate.id}>{candidate.name} — {candidate.id}</option>)
        }
      
      </select>
      
      <span className="candidate-count">{candidates.length} hồ sơ</span>
    </div>

    
    {/* Nội dung chi tiết khi đã có hồ sơ được chọn */}
    {selectedCandidate ? 
      <>
        <CandidateOverview candidate={selectedCandidate} />

        <SummaryCard candidate={selectedCandidate} 
                      percentage={percentage} 
                      counts={counts} />

        <CriteriaList results={results} 
                      visibleResults={visibleResults} 
                      counts={counts} 
                      filter={filter} 
                      setFilter={setFilter} />

        <div className="disclaimer">
          <Icon>ⓘ</Icon><p><strong>Lưu ý: </strong> 
          Tỷ lệ đạt chỉ là thống kê tiêu chí, không tự động thay thế kết luận pháp lý hoặc quyết định của người có thẩm quyền.</p>
        </div>


      </> : <div className="empty-state">Chưa có hồ sơ. Hãy tải lên file JSON ứng viên để bắt đầu.</div>}
  </MainLayout>;
}
