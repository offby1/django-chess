# Android Chess Client - Implementation Plan

## Executive Summary

This document outlines the plan to create a native Android app that acts as a client for the Django Chess web application. The current Django app uses server-side rendering with HTML templates and HTMX, so we'll need to add a REST API layer to support the mobile client.

## Current Backend Analysis

### Application Overview
- **Purpose**: Web-based chess game where users play against an AI opponent
- **Tech Stack**: Django 5.2.5, Python 3.13+, SQLite, python-chess library, GNU Chess AI
- **Deployment**: Docker + Caddy reverse proxy
- **Frontend**: Server-side rendered HTML with HTMX for interactivity

### Data Model
Single model: `Game`
```python
class Game(models.Model):
    id = UUIDField(primary_key=True)          # UUID for privacy
    in_progress = BooleanField(default=True)   # Game status
    moves = CharField(null=True)               # JSON array of UCI strings
    black_smartness = PositiveSmallIntegerField(default=10)  # AI difficulty 0-10
```

### Current Endpoints (HTML-based)
- `GET /` - Home page listing all games
- `GET /game/<uuid>/` - Game display with board
- `POST /game/` - Create new game
- `POST /move/<uuid>/` - Submit a move (UCI format)
- `POST /set-black-smartness/<uuid>/` - Adjust AI difficulty
- `GET /pgn/<uuid>/` - Export game as PGN
- `POST /pgn/` - Import games from PGN file

### Key Implementation Details
1. **Board State**: Reconstructed from move history on each request (not stored as FEN)
2. **Move Format**: UCI notation (e.g., "e2e4", "g1f3")
3. **AI Logic**: GNU Chess engine with configurable smartness (0-10 scale)
4. **Authentication**: None currently implemented (all games publicly accessible via UUID)
5. **Move Validation**: Handled by python-chess library
6. **Pawn Promotion**: Automatic promotion to Queen

---

## Android App Architecture

### Technology Stack

#### Core Framework
- **Language**: Kotlin (modern, idiomatic Android development)
- **Min SDK**: API 26 (Android 8.0) - covers 95%+ of active devices
- **Target SDK**: API 35 (Android 15)
- **Build System**: Gradle with Kotlin DSL

#### Architecture Pattern
- **MVVM (Model-View-ViewModel)** with Clean Architecture principles
- **Single Activity Architecture** with Navigation Component
- **Repository Pattern** for data access abstraction

#### Key Libraries

**Networking & Serialization**
- Retrofit 2.11+ - HTTP client for REST API calls
- OkHttp 4.12+ - HTTP client with interceptors for logging/auth
- Moshi 1.15+ or Kotlinx Serialization - JSON serialization
- Coil 2.5+ - Image loading for piece SVGs (if needed)

**Asynchronous Programming**
- Kotlin Coroutines - Async operations
- Flow - Reactive data streams

**Dependency Injection**
- Hilt (Dagger) - Dependency injection framework

**UI & Navigation**
- Jetpack Compose - Modern declarative UI toolkit
- Navigation Compose - Type-safe navigation
- Material 3 - Material Design components

**Data Persistence**
- Room Database - Local caching of games
- DataStore - Preferences storage (server URL, settings)

**Chess Logic**
- Chess.kt or similar library - For board rendering and move validation
- Alternative: Implement custom chess board view with Canvas

**Testing**
- JUnit 5 - Unit testing
- MockK - Mocking framework
- Turbine - Flow testing
- Compose UI Testing - UI tests

---

## Backend API Requirements

### New REST API Endpoints Needed

The Django backend needs a REST API layer to support the Android app. This can be added alongside existing HTML views.

#### 1. Game List
```
GET /api/games/
Response: 200 OK
{
  "in_progress": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-01-12T10:30:00Z",
      "move_count": 15,
      "black_smartness": 10,
      "whose_turn": "white"
    }
  ],
  "completed": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440001",
      "created_at": "2026-01-11T14:20:00Z",
      "move_count": 42,
      "outcome": "White won by checkmate"
    }
  ]
}
```

#### 2. Create Game
```
POST /api/games/
Request Body: {
  "black_smartness": 10  // Optional, defaults to 10
}
Response: 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "in_progress": true,
  "moves": [],
  "black_smartness": 10,
  "board_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

#### 3. Get Game State
```
GET /api/games/<uuid>/
Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "in_progress": true,
  "moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
  "move_san": ["e4", "e5", "Nf3", "Nc6"],  // Standard Algebraic Notation
  "black_smartness": 10,
  "board_fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
  "whose_turn": "white",
  "legal_moves": ["a2a3", "a2a4", "b2b3", ...],  // All legal moves in UCI
  "captured_pieces": {
    "white": [],
    "black": []
  },
  "outcome": null  // or "White won by checkmate", "Stalemate", etc.
}
```

#### 4. Make Move
```
POST /api/games/<uuid>/moves/
Request Body: {
  "move": "e2e4"  // UCI format
}
Response: 200 OK
{
  "move_made": "e2e4",
  "ai_response": "e7e5",  // null if game ended or White's turn
  "game_state": {
    // Same as Get Game State response
  }
}
```

#### 5. Update AI Difficulty
```
PATCH /api/games/<uuid>/
Request Body: {
  "black_smartness": 5
}
Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "black_smartness": 5
}
```

#### 6. Delete Game
```
DELETE /api/games/<uuid>/
Response: 204 No Content
```

#### 7. Export PGN
```
GET /api/games/<uuid>/pgn/
Response: 200 OK
Content-Type: text/plain
[Event "Casual Game"]
[Site "?"]
[Date "2026.01.12"]
...
```

#### 8. Import PGN
```
POST /api/games/import-pgn/
Request Body: multipart/form-data
  pgn_file: <file>
Response: 201 Created
{
  "games_imported": [
    "550e8400-e29b-41d4-a716-446655440000",
    "650e8400-e29b-41d4-a716-446655440001"
  ]
}
```

### Implementation Options for Backend

#### Option A: Django REST Framework (DRF)
**Recommended approach**
- Add `djangorestframework` to requirements
- Create serializers for Game model
- Create ViewSets with API views
- Keep existing HTML views unchanged
- URL structure: `/api/` prefix for REST endpoints

**Pros:**
- Industry standard, mature framework
- Automatic API documentation (with drf-spectacular)
- Built-in pagination, filtering, permissions
- Minimal changes to existing code

**Cons:**
- Additional dependency

#### Option B: Custom JSON Views
- Modify existing views to check `Accept` header
- Return JSON for `application/json`, HTML otherwise
- Reuse existing logic

**Pros:**
- No new dependencies
- Simpler for small APIs

**Cons:**
- More manual work
- Less standardized
- No automatic documentation

#### Option C: Django Ninja
- Modern, FastAPI-like framework for Django
- Type hints and automatic validation
- Better performance than DRF

**Pros:**
- Modern syntax
- Better performance
- Automatic OpenAPI docs

**Cons:**
- Less mature than DRF
- Different paradigm from existing code

**Recommendation**: Use Django REST Framework (Option A) for robustness and ecosystem support.

---

## Android App Feature Set

### Phase 1: Core Functionality (MVP)

#### 1. Home Screen
- List all games (in-progress and completed)
- Pull-to-refresh for latest games
- "New Game" floating action button
- Click game to view details
- Swipe to delete game

#### 2. Game Screen
- Interactive chess board with pieces
- Display whose turn it is
- Highlight legal moves when piece is selected
- Tap piece to select, tap destination to move
- Show captured pieces for both sides
- Move history list (SAN notation)
- AI difficulty slider (0-10)
- "Resign" button (deletes game or marks as completed)

#### 3. Settings Screen
- Server URL configuration
- Theme selection (Light/Dark/System)
- Board theme (colors, piece set)
- Animation speed

#### 4. Error Handling
- Network error messages
- Retry mechanism
- Offline mode (view cached games, no moves)

### Phase 2: Enhanced Features

#### 1. PGN Support
- Import PGN from file picker
- Export current game as PGN
- Share PGN via system share sheet

#### 2. Game Analysis
- Show board evaluation (if we add Stockfish to backend)
- Highlight best moves
- Suggest improvements

#### 3. Multiplayer (Future)
- WebSocket support for real-time updates
- Play against other humans (requires backend changes)
- User accounts and authentication

#### 4. Offline Play
- Play locally without server (use local chess engine)
- Sync when online
- Conflict resolution

---

## Android App Module Structure

```
com.example.chessclient/
├── data/
│   ├── api/
│   │   ├── ChessApiService.kt           # Retrofit interface
│   │   ├── dto/                         # Data Transfer Objects
│   │   │   ├── GameDto.kt
│   │   │   ├── MoveDto.kt
│   │   │   └── GameListDto.kt
│   │   └── interceptors/
│   │       ├── AuthInterceptor.kt       # Future: auth headers
│   │       └── LoggingInterceptor.kt
│   ├── database/
│   │   ├── ChessDatabase.kt             # Room database
│   │   ├── dao/
│   │   │   └── GameDao.kt
│   │   └── entities/
│   │       └── GameEntity.kt
│   ├── repository/
│   │   ├── GameRepository.kt            # Interface
│   │   └── GameRepositoryImpl.kt        # Implementation
│   └── preferences/
│       └── UserPreferences.kt           # DataStore wrapper
├── domain/
│   ├── model/
│   │   ├── Game.kt                      # Domain model
│   │   ├── Move.kt
│   │   ├── Square.kt
│   │   └── Piece.kt
│   ├── usecase/
│   │   ├── GetGamesUseCase.kt
│   │   ├── CreateGameUseCase.kt
│   │   ├── MakeMoveUseCase.kt
│   │   └── UpdateAIDifficultyUseCase.kt
│   └── Result.kt                        # Sealed class for API results
├── ui/
│   ├── theme/
│   │   ├── Theme.kt
│   │   ├── Color.kt
│   │   └── Type.kt
│   ├── components/
│   │   ├── ChessBoard.kt                # Composable chess board
│   │   ├── ChessPiece.kt
│   │   ├── MoveHistoryList.kt
│   │   └── CapturedPiecesList.kt
│   ├── screens/
│   │   ├── home/
│   │   │   ├── HomeScreen.kt
│   │   │   ├── HomeViewModel.kt
│   │   │   └── GameListItem.kt
│   │   ├── game/
│   │   │   ├── GameScreen.kt
│   │   │   ├── GameViewModel.kt
│   │   │   └── GameUiState.kt
│   │   └── settings/
│   │       ├── SettingsScreen.kt
│   │       └── SettingsViewModel.kt
│   ├── navigation/
│   │   └── ChessNavGraph.kt
│   └── MainActivity.kt
├── di/
│   ├── AppModule.kt                     # Hilt modules
│   ├── NetworkModule.kt
│   └── DatabaseModule.kt
└── util/
    ├── ChessNotationConverter.kt        # UCI <-> SAN conversion
    ├── PgnParser.kt
    └── Extensions.kt

res/
├── drawable/
│   └── chess_pieces/                    # SVG/Vector drawables for pieces
│       ├── ic_white_king.xml
│       ├── ic_white_queen.xml
│       └── ...
├── values/
│   ├── strings.xml
│   ├── colors.xml
│   └── themes.xml
└── navigation/
    └── nav_graph.xml
```

---

## Detailed Implementation Plan

### Step 1: Backend API Layer (Django)

#### 1.1 Install Dependencies
```bash
pip install djangorestframework
pip install drf-spectacular  # For API docs
```

#### 1.2 Create API App
```bash
python manage.py startapp api
```

#### 1.3 Create Serializers
```python
# django_chess/api/serializers.py
from rest_framework import serializers
from django_chess.app.models import Game

class GameSerializer(serializers.ModelSerializer):
    move_san = serializers.SerializerMethodField()
    board_fen = serializers.SerializerMethodField()
    whose_turn = serializers.SerializerMethodField()
    legal_moves = serializers.SerializerMethodField()
    captured_pieces = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'in_progress', 'moves', 'move_san', 'black_smartness',
                  'board_fen', 'whose_turn', 'legal_moves', 'captured_pieces', 'outcome']
        read_only_fields = ['id', 'moves', 'move_san', 'board_fen', 'whose_turn',
                           'legal_moves', 'captured_pieces', 'outcome']
```

#### 1.4 Create ViewSets
```python
# django_chess/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    @action(detail=True, methods=['post'])
    def moves(self, request, pk=None):
        # Handle move submission
        pass

    @action(detail=True, methods=['get'])
    def pgn(self, request, pk=None):
        # Export PGN
        pass

    @action(detail=False, methods=['post'])
    def import_pgn(self, request):
        # Import PGN
        pass
```

#### 1.5 Update URLs
```python
# django_chess/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'games', GameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# django_chess/urls.py - add:
path('api/', include('django_chess.api.urls')),
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
```

#### 1.6 Add CORS Support
```bash
pip install django-cors-headers
```

```python
# django_chess/base_settings.py
INSTALLED_APPS += ['corsheaders']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE
CORS_ALLOW_ALL_ORIGINS = True  # For development; restrict in production
```

### Step 2: Android Project Setup

#### 2.1 Create Android Project
- Android Studio: New Project -> Empty Compose Activity
- Package name: `com.example.chessclient`
- Language: Kotlin
- Minimum SDK: API 26

#### 2.2 Configure Gradle Dependencies
```kotlin
// build.gradle.kts (app module)
dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")

    // Compose
    implementation(platform("androidx.compose:compose-bom:2024.01.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.6")

    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // JSON
    implementation("com.squareup.moshi:moshi:1.15.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.0")
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.0")

    // Dependency Injection
    implementation("com.google.dagger:hilt-android:2.50")
    ksp("com.google.dagger:hilt-compiler:2.50")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

    // Database
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // DataStore
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("app.cash.turbine:turbine:1.0.0")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
}
```

#### 2.3 Configure Hilt
```kotlin
// Application class
@HiltAndroidApp
class ChessApplication : Application()
```

```xml
<!-- AndroidManifest.xml -->
<application
    android:name=".ChessApplication"
    android:usesCleartextTraffic="true"  <!-- For local development -->
    ...>
```

### Step 3: Data Layer Implementation

#### 3.1 API Service
```kotlin
interface ChessApiService {
    @GET("api/games/")
    suspend fun getGames(): GameListResponse

    @POST("api/games/")
    suspend fun createGame(@Body request: CreateGameRequest): GameResponse

    @GET("api/games/{id}/")
    suspend fun getGame(@Path("id") gameId: String): GameResponse

    @POST("api/games/{id}/moves/")
    suspend fun makeMove(@Path("id") gameId: String, @Body move: MoveRequest): MoveResponse

    @PATCH("api/games/{id}/")
    suspend fun updateGame(@Path("id") gameId: String, @Body update: UpdateGameRequest): GameResponse

    @DELETE("api/games/{id}/")
    suspend fun deleteGame(@Path("id") gameId: String): Response<Unit>

    @GET("api/games/{id}/pgn/")
    suspend fun exportPgn(@Path("id") gameId: String): ResponseBody

    @Multipart
    @POST("api/games/import-pgn/")
    suspend fun importPgn(@Part file: MultipartBody.Part): ImportPgnResponse
}
```

#### 3.2 Repository
```kotlin
interface GameRepository {
    fun getGames(): Flow<Result<List<Game>>>
    suspend fun createGame(aiDifficulty: Int): Result<Game>
    fun getGame(gameId: String): Flow<Result<Game>>
    suspend fun makeMove(gameId: String, move: String): Result<Game>
    suspend fun updateAIDifficulty(gameId: String, difficulty: Int): Result<Unit>
    suspend fun deleteGame(gameId: String): Result<Unit>
    suspend fun exportPgn(gameId: String): Result<String>
    suspend fun importPgn(uri: Uri): Result<List<String>>
}

class GameRepositoryImpl @Inject constructor(
    private val apiService: ChessApiService,
    private val gameDao: GameDao
) : GameRepository {
    // Implementation with caching strategy
}
```

#### 3.3 Room Database
```kotlin
@Entity(tableName = "games")
data class GameEntity(
    @PrimaryKey val id: String,
    val inProgress: Boolean,
    val moves: String,  // JSON
    val blackSmartness: Int,
    val cachedAt: Long
)

@Dao
interface GameDao {
    @Query("SELECT * FROM games ORDER BY cachedAt DESC")
    fun getAll(): Flow<List<GameEntity>>

    @Query("SELECT * FROM games WHERE id = :id")
    fun getById(id: String): Flow<GameEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(game: GameEntity)

    @Delete
    suspend fun delete(game: GameEntity)
}
```

### Step 4: Domain Layer

#### 4.1 Domain Models
```kotlin
data class Game(
    val id: String,
    val inProgress: Boolean,
    val moves: List<String>,  // UCI moves
    val moveSan: List<String>,  // SAN moves for display
    val blackSmartness: Int,
    val boardFen: String,
    val whoseTurn: Player,
    val legalMoves: List<String>,
    val capturedPieces: CapturedPieces,
    val outcome: String?
)

enum class Player { WHITE, BLACK }

data class CapturedPieces(
    val white: List<String>,
    val black: List<String>
)

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    object Loading : Result<Nothing>()
}
```

#### 4.2 Use Cases
```kotlin
class GetGamesUseCase @Inject constructor(
    private val repository: GameRepository
) {
    operator fun invoke(): Flow<Result<List<Game>>> = repository.getGames()
}

class MakeMoveUseCase @Inject constructor(
    private val repository: GameRepository
) {
    suspend operator fun invoke(gameId: String, move: String): Result<Game> {
        return repository.makeMove(gameId, move)
    }
}
```

### Step 5: UI Layer

#### 5.1 Chess Board Composable
```kotlin
@Composable
fun ChessBoard(
    board: Board,
    selectedSquare: Square?,
    legalMoves: List<String>,
    onSquareClick: (Square) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(8),
        modifier = modifier.aspectRatio(1f)
    ) {
        items(64) { index ->
            val rank = 7 - (index / 8)
            val file = index % 8
            val square = Square(rank, file)

            ChessSquare(
                square = square,
                piece = board.pieceAt(square),
                isLight = (rank + file) % 2 == 0,
                isSelected = square == selectedSquare,
                isLegalMove = legalMoves.contains(square.toUci()),
                isLastMove = board.lastMove?.contains(square) == true,
                onClick = { onSquareClick(square) }
            )
        }
    }
}

@Composable
fun ChessSquare(
    square: Square,
    piece: Piece?,
    isLight: Boolean,
    isSelected: Boolean,
    isLegalMove: Boolean,
    isLastMove: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .aspectRatio(1f)
            .background(
                when {
                    isSelected -> Color.Yellow.copy(alpha = 0.5f)
                    isLastMove -> Color.Green.copy(alpha = 0.3f)
                    isLight -> Color(0xFFEEEED2)
                    else -> Color(0xFF769656)
                }
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        if (isLegalMove && piece == null) {
            // Draw small circle for empty legal move squares
            Box(
                modifier = Modifier
                    .size(16.dp)
                    .background(Color.Black.copy(alpha = 0.2f), CircleShape)
            )
        }

        piece?.let {
            Text(
                text = it.unicode,
                fontSize = 48.sp
            )
        }

        if (isLegalMove && piece != null) {
            // Draw border for capturable pieces
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .border(4.dp, Color.Red.copy(alpha = 0.5f))
            )
        }
    }
}
```

#### 5.2 Game Screen ViewModel
```kotlin
@HiltViewModel
class GameViewModel @Inject constructor(
    private val getGameUseCase: GetGameUseCase,
    private val makeMoveUseCase: MakeMoveUseCase,
    private val updateAIDifficultyUseCase: UpdateAIDifficultyUseCase,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val gameId: String = checkNotNull(savedStateHandle["gameId"])

    private val _uiState = MutableStateFlow<GameUiState>(GameUiState.Loading)
    val uiState: StateFlow<GameUiState> = _uiState.asStateFlow()

    private val _selectedSquare = MutableStateFlow<Square?>(null)
    val selectedSquare: StateFlow<Square?> = _selectedSquare.asStateFlow()

    init {
        loadGame()
    }

    private fun loadGame() {
        viewModelScope.launch {
            getGameUseCase(gameId).collect { result ->
                _uiState.value = when (result) {
                    is Result.Success -> GameUiState.Success(result.data)
                    is Result.Error -> GameUiState.Error(result.exception.message ?: "Unknown error")
                    is Result.Loading -> GameUiState.Loading
                }
            }
        }
    }

    fun onSquareClick(square: Square) {
        val currentState = _uiState.value as? GameUiState.Success ?: return
        val game = currentState.game

        when (val selected = _selectedSquare.value) {
            null -> {
                // Select piece if it's movable
                if (game.legalMoves.any { it.startsWith(square.toUci()) }) {
                    _selectedSquare.value = square
                }
            }
            else -> {
                // Try to make move
                val move = "${selected.toUci()}${square.toUci()}"
                if (game.legalMoves.contains(move)) {
                    makeMove(move)
                }
                _selectedSquare.value = null
            }
        }
    }

    private fun makeMove(move: String) {
        viewModelScope.launch {
            when (val result = makeMoveUseCase(gameId, move)) {
                is Result.Success -> {
                    // UI will update via Flow
                }
                is Result.Error -> {
                    // Show error
                }
            }
        }
    }

    fun updateAIDifficulty(difficulty: Int) {
        viewModelScope.launch {
            updateAIDifficultyUseCase(gameId, difficulty)
        }
    }
}

sealed class GameUiState {
    object Loading : GameUiState()
    data class Success(val game: Game) : GameUiState()
    data class Error(val message: String) : GameUiState()
}
```

#### 5.3 Game Screen
```kotlin
@Composable
fun GameScreen(
    viewModel: GameViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val selectedSquare by viewModel.selectedSquare.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Chess Game") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        when (val state = uiState) {
            is GameUiState.Loading -> {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
            is GameUiState.Error -> {
                ErrorView(message = state.message, onRetry = { viewModel.loadGame() })
            }
            is GameUiState.Success -> {
                GameContent(
                    game = state.game,
                    selectedSquare = selectedSquare,
                    onSquareClick = viewModel::onSquareClick,
                    onAIDifficultyChange = viewModel::updateAIDifficulty,
                    modifier = Modifier.padding(padding)
                )
            }
        }
    }
}

@Composable
fun GameContent(
    game: Game,
    selectedSquare: Square?,
    onSquareClick: (Square) -> Unit,
    onAIDifficultyChange: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Status bar
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Text("Turn: ${game.whoseTurn}", style = MaterialTheme.typography.titleMedium)
                game.outcome?.let {
                    Text("Outcome: $it", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Chess board
        ChessBoard(
            board = game.toBoard(),
            selectedSquare = selectedSquare,
            legalMoves = game.legalMoves,
            onSquareClick = onSquareClick,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(Modifier.height(16.dp))

        // AI Difficulty slider
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Text("AI Difficulty: ${game.blackSmartness}")
                Slider(
                    value = game.blackSmartness.toFloat(),
                    onValueChange = { onAIDifficultyChange(it.toInt()) },
                    valueRange = 0f..10f,
                    steps = 9
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // Move history
        Card(modifier = Modifier.fillMaxWidth().weight(1f)) {
            LazyColumn(Modifier.padding(16.dp)) {
                items(game.moveSan.chunked(2)) { movePair ->
                    Row {
                        Text("${movePair[0]}  ", Modifier.weight(1f))
                        if (movePair.size > 1) {
                            Text(movePair[1], Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}
```

#### 5.4 Home Screen
```kotlin
@Composable
fun HomeScreen(
    viewModel: HomeViewModel = hiltViewModel(),
    onGameClick: (String) -> Unit,
    onCreateGame: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Chess Games") })
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onCreateGame) {
                Icon(Icons.Default.Add, "New Game")
            }
        }
    ) { padding ->
        when (val state = uiState) {
            is HomeUiState.Loading -> LoadingView()
            is HomeUiState.Error -> ErrorView(state.message)
            is HomeUiState.Success -> {
                GameList(
                    inProgressGames = state.inProgressGames,
                    completedGames = state.completedGames,
                    onGameClick = onGameClick,
                    modifier = Modifier.padding(padding)
                )
            }
        }
    }
}
```

### Step 6: Testing Strategy

#### 6.1 Unit Tests
- Repository tests with mocked API service
- ViewModel tests with mocked repository
- Use case tests

#### 6.2 Integration Tests
- API service tests against real backend
- Database tests

#### 6.3 UI Tests
- Compose UI tests for screens
- Navigation tests

---

## Configuration & Deployment

### Server URL Configuration

#### Option 1: Hardcoded (Development)
```kotlin
object ApiConfig {
    const val BASE_URL = "http://10.0.2.2:8000/"  // Android emulator -> localhost
    // const val BASE_URL = "https://chess.offby1.info/"  // Production
}
```

#### Option 2: Settings Screen (Recommended)
- Store base URL in DataStore
- Allow user to configure custom server
- Default to production URL
- Provide "Local Development" quick option

### Build Variants
```kotlin
// build.gradle.kts
android {
    buildTypes {
        debug {
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/\"")
        }
        release {
            buildConfigField("String", "API_BASE_URL", "\"https://chess.offby1.info/\"")
        }
    }
}
```

---

## Timeline & Milestones

### Backend API Development
1. **Setup** (2-4 hours)
   - Install DRF, configure CORS
   - Create API app structure
   - Add serializers

2. **Endpoints** (4-6 hours)
   - Implement ViewSets
   - Add move handling logic
   - PGN import/export endpoints
   - Testing with Postman/curl

3. **Documentation** (1-2 hours)
   - OpenAPI schema with drf-spectacular
   - Test all endpoints

### Android App Development
1. **Project Setup** (2-3 hours)
   - Create project
   - Configure dependencies
   - Setup Hilt

2. **Data Layer** (6-8 hours)
   - API service definitions
   - Repository implementation
   - Room database
   - DataStore preferences

3. **Domain Layer** (3-4 hours)
   - Domain models
   - Use cases
   - Result types

4. **UI - Home Screen** (4-5 hours)
   - Game list UI
   - Create game flow
   - Navigation setup

5. **UI - Game Screen** (10-12 hours)
   - Chess board component
   - Piece rendering
   - Move logic
   - AI difficulty slider
   - Move history

6. **Settings & Polish** (3-4 hours)
   - Settings screen
   - Themes
   - Error handling

7. **Testing** (6-8 hours)
   - Unit tests
   - Integration tests
   - UI tests

**Total Estimated Time**: 40-55 hours

---

## Future Enhancements

### Phase 3: Advanced Features
1. **User Authentication**
   - Django user accounts
   - JWT tokens
   - Login/register screens

2. **Real-time Multiplayer**
   - WebSocket support (Django Channels)
   - Play against other humans
   - Game invitations

3. **Advanced Chess Features**
   - Stockfish integration for analysis
   - Opening book
   - Puzzle mode
   - Custom time controls

4. **Social Features**
   - User profiles
   - Game sharing
   - Leaderboards
   - Friend system

5. **Offline Mode**
   - Local chess engine
   - Offline play
   - Sync when online

---

## Technical Considerations

### Chess Logic
**Option A**: Use existing library (Chess.kt or similar)
- Pros: Faster development, battle-tested
- Cons: Dependency on third-party library

**Option B**: Implement custom chess logic
- Pros: Full control, learning opportunity
- Cons: Complex, error-prone, time-consuming

**Recommendation**: Use library for MVP, consider custom implementation later if needed.

### Board Rendering
**Option A**: Compose Canvas
- Draw board and pieces manually
- Full control over animations
- More complex

**Option B**: LazyGrid with Unicode characters
- Simple, fast to implement
- Limited animation options
- Good for MVP

**Option C**: Custom View with Canvas (XML)
- Traditional Android approach
- More complex with Compose interop

**Recommendation**: LazyGrid with Unicode (Option B) for MVP, Canvas for Phase 2.

### State Management
- Use StateFlow for UI state
- Use Flow for data streams
- MVI pattern optional for complex screens

### Error Handling
- Network errors (timeout, no connection)
- API errors (400, 404, 500)
- Invalid moves
- Game not found

### Performance
- Cache games locally
- Lazy load game list
- Debounce AI difficulty slider
- Use remember {} for board calculations

---

## Dependencies & Requirements

### Backend Requirements
- Python 3.13+
- Django 5.2.5
- djangorestframework 3.14+
- drf-spectacular 0.27+ (optional, for docs)
- django-cors-headers 4.3+

### Android Requirements
- Android Studio Hedgehog or newer
- Kotlin 1.9+
- Gradle 8.2+
- Min SDK 26 (covers 95%+ devices)
- Target SDK 35

### Development Tools
- Postman/Insomnia for API testing
- Android Emulator or physical device
- Git for version control

---

## Security Considerations

### Current State (No Auth)
- Games accessible by UUID (security through obscurity)
- CORS open to all origins
- No rate limiting

### Recommendations for Production
1. **Add Authentication**
   - User accounts
   - JWT tokens
   - Associate games with users

2. **Restrict CORS**
   - Limit to known origins
   - Proper CORS configuration

3. **Add Rate Limiting**
   - Prevent API abuse
   - Django-ratelimit or DRF throttling

4. **Input Validation**
   - Already handled by python-chess
   - Add extra validation in API layer

5. **HTTPS Only**
   - Already configured with Caddy
   - Ensure Android app uses HTTPS in production

---

## Conclusion

This plan provides a comprehensive roadmap for creating an Android client for the Django Chess application. The approach is:

1. **Backend-First**: Add REST API layer to Django (minimal changes to existing code)
2. **Android MVP**: Focus on core gameplay features first
3. **Iterative**: Build in phases, test frequently
4. **Extensible**: Architecture supports future enhancements

The estimated timeline is realistic for a developer familiar with Django and Android/Kotlin. The modular design allows for parallel development of backend and frontend once the API contract is established.

**Next Steps**:
1. Review and approve this plan
2. Create new Android project repository
3. Implement Django REST API
4. Begin Android development
5. Iterate based on testing and feedback
