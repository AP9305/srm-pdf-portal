# 🎓 SRMIST Syllabus Extractor Portal

A stunning web application that allows educators to search and extract specific subject syllabi from the complete 587-page SRMIST Computing Programmes Syllabus 2021 PDF.

## ✨ Features

- **🔍 Smart Search**: Fuzzy matching algorithm handles typos and partial matches
- **📄 Full PDF Coverage**: Searches all 587 pages of the syllabus document
- **🎨 Beautiful UI**: Modern, responsive design with animations and glass morphism effects
- **⚡ Lightning Fast**: Cached PDF processing for instant results
- **📱 Mobile Friendly**: Fully responsive design works on all devices
- **🔗 Direct Download**: One-click download of extracted syllabus pages
- **💡 Smart Suggestions**: Auto-complete for common subjects

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd windsurf-project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:8000`

## 🎯 How to Use

1. **Enter Subject Name**: Type any subject from the computing syllabus (e.g., "Software Testing", "Machine Learning")
2. **Smart Suggestions**: Use the auto-complete suggestions for common subjects
3. **Search**: Click "Extract Syllabus Pages" or press Enter
4. **Download**: Once found, click the download button to get your PDF

## 🔧 Technical Details

### Backend Architecture
- **FastAPI**: Modern, fast web framework for building APIs
- **PyPDF2**: PDF processing and manipulation
- **FuzzyWuzzy**: Intelligent text matching with typo tolerance
- **Caching**: In-memory PDF caching to avoid repeated downloads

### Frontend Features
- **React**: Component-based UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Glass Morphism**: Modern UI design trend
- **Animations**: Smooth transitions and micro-interactions
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile

### Search Algorithm
1. Downloads the 587-page SRMIST syllabus PDF
2. Extracts text from each page
3. Uses fuzzy matching to find relevant pages
4. Boosts scores for pages with course codes (21CS/21CE pattern)
5. Includes adjacent pages if content spans multiple pages
6. Compiles matching pages into a downloadable mini-PDF

## 📚 Example Searches

Try searching for these subjects:
- Software Testing
- Artificial Intelligence
- Data Structures
- Machine Learning
- Database Management Systems
- Computer Networks
- Operating Systems
- Web Development
- Mobile Computing
- Cyber Security

## 🛠️ API Endpoints

### `POST /api/search`
Search for a subject in the syllabus
```json
{
  "subject": "Software Testing"
}
```

### `GET /api/download/{filename}`
Download the extracted PDF file

### `GET /api/health`
Health check endpoint

## 🎨 UI Components

- **Animated Background**: Floating particles for visual appeal
- **Glass Effect Cards**: Modern frosted glass appearance
- **Smart Input**: Auto-complete with suggestions
- **Loading States**: Beautiful loading animations
- **Success/Error Messages**: Clear feedback with icons
- **Download Button**: Prominent call-to-action

## 🔒 Security Features

- Input validation and sanitization
- Temporary file cleanup after download
- CORS protection
- Request timeout handling
- Error logging and monitoring

## 🚀 Deployment Options

### Local Development
```bash
python app.py
```

### Production Deployment
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📁 Project Structure

```
windsurf-project/
├── app.py                 # FastAPI backend application
├── static/
│   └── index.html        # React frontend with Tailwind CSS
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🐛 Troubleshooting

### Common Issues

1. **PDF Download Fails**
   - Check internet connection
   - Verify the SRMIST PDF URL is accessible

2. **No Search Results**
   - Try different keywords or spellings
   - Use broader terms (e.g., "AI" instead of "Artificial Intelligence")

3. **Port Already in Use**
   - Change the port in `app.py`: `uvicorn.run(app, port=8001)`

### Error Messages

- **"Please enter a subject name"**: Input field is empty
- **"No pages found"**: Subject not found in the syllabus
- **"Network error"**: Connection issues with the PDF source
- **"File not found"**: Download link expired (regenerate search)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- SRMIST for providing the comprehensive syllabus document
- FastAPI and React communities for excellent frameworks
- Tailwind CSS for beautiful styling utilities

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Create an issue in the repository

---

**Built with ❤️ for educators and students at SRMIST**
