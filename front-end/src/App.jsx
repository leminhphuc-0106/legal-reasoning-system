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
// import { normalizeCandidate, readJsonFile } from "./utils/normalize.js";
import { askAssistant } from "./services/chatService.js";
// import { handleEvaluate } from "./services/evalService.js";
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
  const [candidateFiles, setCandidateFiles] = useState([]);

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
  // Xử lý khi người dùng tải lên một hoặc nhiều tài liệu pháp luật.
  // Xử lý khi người dùng tải lên một tài liệu pháp luật PDF.
  function handleLawUpload(event) {

      // Lấy file đầu tiên người dùng chọn.
      const file = event.target.files?.[0];

      // Nếu người dùng không chọn file thì kết thúc hàm.
      if (!file) return;

      // Kiểm tra định dạng file, chỉ chấp nhận PDF.
      if (!file.name.toLowerCase().endsWith(".pdf")) {
          setNotice("Vui lòng chỉ chọn file PDF.");
          event.target.value = "";
          return;
      }

      // Cập nhật danh sách tài liệu pháp luật.
      // Mỗi lần tải lên, thay thế tài liệu cũ bằng tài liệu mới.
      setLawFiles([file]);

      setNotice(`Đã thêm tài liệu pháp luật: ${file.name}`);

      // Reset input để có thể chọn lại cùng một file.
      event.target.value = "";
  }



  // Đọc một hoặc nhiều file JSON hồ sơ ứng viên,
  // chuẩn hóa dữ liệu và gộp vào danh sách ứng viên hiện tại.
  // Xử lý khi người dùng chọn file hoặc thư mục hồ sơ.
  function handleCandidateUpload(event) {
      // Lấy danh sách file từ input.
      const files = Array.from(event.target.files ?? []);

      // Nếu không có file thì kết thúc.
      if (!files.length) return;

      // Thêm các file mới vào danh sách hồ sơ hiện tại.
      setCandidateFiles(previous => [...previous, ...files]);

      // In danh sách file ra console để kiểm tra.
      console.log("Các hồ sơ vừa thêm:", files);

      // In tên từng file.
      files.forEach(file => {
          console.log(file.name);
      });

      // Reset input để có thể chọn lại cùng một file.
      event.target.value = "";
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

    // Xét hồ sơ: nơi sẽ gọi API chạy toàn bộ pipeline xử lý.
    // Hiện backend chưa có nên tạm thời in dữ liệu đầu vào ra console.
  async function handleEvaluate() {
      try {
          // Bật trạng thái loading
          setIsLoading(true);
          setNotice("Đang gửi hồ sơ lên hệ thống...");

          await sleep(1000); // Giả lập độ trễ để thấy spinner loading

          // Kiểm tra file tiêu chí
          if (!lawFiles.length) {
              throw new Error("Vui lòng chọn file PDF tiêu chí xét thưởng.");
          }

          // Kiểm tra danh sách hồ sơ ứng viên
          if (!candidateFiles.length) {
              throw new Error("Vui lòng thêm hồ sơ ứng viên.");
          }

          // Tạo FormData để gửi file lên FastAPI
          const formData = new FormData();

          // Thêm file tiêu chí
          formData.append("criteria_file", lawFiles[0]);
          console.log("Đã thêm file tiêu chí:", lawFiles[0].name);

          // Thêm danh sách file ứng viên
          candidateFiles.forEach(file => {
              formData.append("candidate_files", file);
              console.log("Đã thêm file ứng viên:", file.name);
          });
          console.log("Tổng số hồ sơ ứng viên:", candidateFiles.length);

          // Gửi request đến FastAPI
          const response = await fetch("http://127.0.0.1:8000/api/evaluate", {
              method: "POST",
              body: formData
          });

          // Nhận kết quả trả về
          const result = await response.json();

          // Kiểm tra lỗi từ backend
          if (!response.ok) {
              console.error("Backend trả về:", result);
              throw new Error(
                  JSON.stringify(result.detail)
              );
          }
          // In kết quả
          console.log("Kết quả xét hồ sơ:", result);

          setNotice("Đã hoàn tất xét hồ sơ!");

      } catch (error) {
          console.error("Lỗi xét hồ sơ:", error);
          setNotice(`Lỗi: ${error.message}`);

      } finally {
          // Tắt loading dù thành công hay thất bại
          setIsLoading(false);
      }
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
    onClearLawFiles={() => setLawFiles([])} 

    candidateFiles={candidateFiles}
    onClearCandidateFiles={() => setCandidateFiles([])}/>

    
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
