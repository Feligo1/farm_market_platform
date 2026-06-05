#!/usr/bin/env python3
"""
FarmConnect Android Project Generator
Run this script to create all necessary files for the Android app
"""

import os
import sys

def create_directories():
    """Create all necessary directories"""
    dirs = [
        "FarmConnect/app/src/main/java/com/farmconnect/activities",
        "FarmConnect/app/src/main/java/com/farmconnect/adapters",
        "FarmConnect/app/src/main/java/com/farmconnect/models",
        "FarmConnect/app/src/main/java/com/farmconnect/network",
        "FarmConnect/app/src/main/java/com/farmconnect/utils",
        "FarmConnect/app/src/main/java/com/farmconnect/services",
        "FarmConnect/app/src/main/res/layout",
        "FarmConnect/app/src/main/res/drawable",
        "FarmConnect/app/src/main/res/values",
        "FarmConnect/app/src/main/res/menu",
        "FarmConnect/app/src/main/res/xml",
        "FarmConnect/gradle/wrapper"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created: {dir_path}")

def write_file(filepath, content):
    """Write content to file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {filepath}")

def generate_gradle_files():
    """Generate all Gradle files"""
    
    # settings.gradle
    write_file("FarmConnect/settings.gradle", '''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url 'https://jitpack.io' }
    }
}
rootProject.name = "FarmConnect"
include ':app'
''')
    
    # build.gradle (project)
    write_file("FarmConnect/build.gradle", '''// Top-level build file
plugins {
    id 'com.android.application' version '8.1.0' apply false
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
''')
    
    # build.gradle (app)
    write_file("FarmConnect/app/build.gradle", '''plugins {
    id 'com.android.application'
}

android {
    namespace 'com.farmconnect'
    compileSdk 34

    defaultConfig {
        applicationId "com.farmconnect"
        minSdk 21
        targetSdk 34
        versionCode 1
        versionName "1.0"

        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.10.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
    implementation 'com.github.bumptech.glide:glide:4.16.0'
    implementation 'com.github.PhilJay:MPAndroidChart:v3.1.0'
    implementation 'androidx.swiperefreshlayout:swiperefreshlayout:1.1.0'
    implementation 'androidx.cardview:cardview:1.0.0'
    implementation 'androidx.recyclerview:recyclerview:1.3.2'
    implementation 'androidx.room:room-runtime:2.6.0'
    annotationProcessor 'androidx.room:room-compiler:2.6.0'
    implementation 'androidx.work:work-runtime:2.9.0'
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}
''')
    
    # gradle-wrapper.properties
    write_file("FarmConnect/gradle/wrapper/gradle-wrapper.properties", '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.0-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
''')
    
    # proguard-rules.pro
    write_file("FarmConnect/app/proguard-rules.pro", '''# Add project specific ProGuard rules here.
# Keep FarmConnect models
-keep class com.farmconnect.models.** { *; }
''')

def generate_manifest():
    """Generate AndroidManifest.xml"""
    write_file("FarmConnect/app/src/main/AndroidManifest.xml", '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_farmconnect_logo"
        android:label="FarmConnect Zambia"
        android:theme="@style/Theme.FarmConnect"
        android:usesCleartextTraffic="true"
        tools:targetApi="31">
        
        <activity
            android:name=".activities.SplashActivity"
            android:exported="true"
            android:theme="@style/Theme.AppCompat.Light.NoActionBar">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        
        <activity android:name=".activities.LoginActivity" />
        <activity android:name=".activities.RegisterActivity" />
        <activity android:name=".activities.MainActivity" />
        <activity android:name=".activities.MarketPricesActivity" />
        <activity android:name=".activities.PriceForecastActivity" />
        <activity android:name=".activities.BuyersActivity" />
        <activity android:name=".activities.ProfileActivity" />
        
    </application>

</manifest>
''')

def generate_models():
    """Generate model classes"""
    
    # User.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/models/User.java", '''package com.farmconnect.models;

import com.google.gson.annotations.SerializedName;

public class User {
    @SerializedName("user_id")
    private String userId;
    
    @SerializedName("username")
    private String username;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("role")
    private String role;
    
    @SerializedName("phone")
    private String phone;
    
    @SerializedName("email")
    private String email;
    
    @SerializedName("location")
    private String location;
    
    @SerializedName("token")
    private String token;
    
    // Getters and Setters
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }
    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
}
''')
    
    # MarketPrice.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/models/MarketPrice.java", '''package com.farmconnect.models;

import com.google.gson.annotations.SerializedName;

public class MarketPrice {
    @SerializedName("id")
    private int id;
    
    @SerializedName("market")
    private String market;
    
    @SerializedName("commodity")
    private String commodity;
    
    @SerializedName("price")
    private double price;
    
    @SerializedName("unit")
    private String unit;
    
    @SerializedName("recorded_at")
    private String recordedAt;
    
    @SerializedName("price_trend")
    private String priceTrend;
    
    // Getters and Setters
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public String getMarket() { return market; }
    public void setMarket(String market) { this.market = market; }
    public String getCommodity() { return commodity; }
    public void setCommodity(String commodity) { this.commodity = commodity; }
    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }
    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }
    public String getRecordedAt() { return recordedAt; }
    public void setRecordedAt(String recordedAt) { this.recordedAt = recordedAt; }
    public String getPriceTrend() { return priceTrend; }
    public void setPriceTrend(String priceTrend) { this.priceTrend = priceTrend; }
}
''')
    
    # Buyer.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/models/Buyer.java", '''package com.farmconnect.models;

import com.google.gson.annotations.SerializedName;

public class Buyer {
    @SerializedName("id")
    private int id;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("phone")
    private String phone;
    
    @SerializedName("commodity")
    private String commodity;
    
    @SerializedName("location")
    private String location;
    
    @SerializedName("max_price")
    private double maxPrice;
    
    @SerializedName("rating")
    private double rating;
    
    // Getters and Setters
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getCommodity() { return commodity; }
    public void setCommodity(String commodity) { this.commodity = commodity; }
    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }
    public double getMaxPrice() { return maxPrice; }
    public void setMaxPrice(double maxPrice) { this.maxPrice = maxPrice; }
    public double getRating() { return rating; }
    public void setRating(double rating) { this.rating = rating; }
}
''')
    
    # Forecast.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/models/Forecast.java", '''package com.farmconnect.models;

import com.google.gson.annotations.SerializedName;

public class Forecast {
    @SerializedName("date")
    private String date;
    
    @SerializedName("predicted_price")
    private double predictedPrice;
    
    @SerializedName("change_percent")
    private double changePercent;
    
    @SerializedName("trend")
    private String trend;
    
    // Getters and Setters
    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }
    public double getPredictedPrice() { return predictedPrice; }
    public void setPredictedPrice(double predictedPrice) { this.predictedPrice = predictedPrice; }
    public double getChangePercent() { return changePercent; }
    public void setChangePercent(double changePercent) { this.changePercent = changePercent; }
    public String getTrend() { return trend; }
    public void setTrend(String trend) { this.trend = trend; }
}
''')

def generate_network():
    """Generate network classes"""
    
    # ApiInterface.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/network/ApiInterface.java", '''package com.farmconnect.network;

import com.farmconnect.models.*;
import retrofit2.Call;
import retrofit2.http.*;
import java.util.List;
import java.util.Map;

public interface ApiInterface {
    @POST("api/login")
    Call<ApiResponse<User>> login(@Body Map<String, String> credentials);
    
    @POST("api/register")
    Call<ApiResponse<User>> register(@Body Map<String, String> userData);
    
    @GET("api/prices")
    Call<ApiResponse<List<MarketPrice>>> getPrices(
        @Query("commodity") String commodity,
        @Query("market") String market,
        @Query("limit") int limit
    );
    
    @GET("api/forecast")
    Call<ApiResponse<List<Forecast>>> getForecast(
        @Query("commodity") String commodity,
        @Query("market") String market,
        @Query("days") int days
    );
    
    @GET("api/buyers")
    Call<ApiResponse<List<Buyer>>> getBuyers(
        @Query("commodity") String commodity,
        @Query("limit") int limit
    );
    
    @GET("api/status")
    Call<ApiResponse<Map<String, Object>>> getStatus();
}
''')
    
    # ApiClient.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/network/ApiClient.java", '''package com.farmconnect.network;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import java.util.concurrent.TimeUnit;

public class ApiClient {
    private static final String BASE_URL = "http://10.0.2.2:5000/";
    private static Retrofit retrofit = null;
    private static ApiInterface apiInterface = null;
    
    public static ApiInterface getClient() {
        if (apiInterface == null) {
            HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
            logging.setLevel(HttpLoggingInterceptor.Level.BODY);
            
            OkHttpClient client = new OkHttpClient.Builder()
                    .addInterceptor(logging)
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(30, TimeUnit.SECONDS)
                    .writeTimeout(30, TimeUnit.SECONDS)
                    .build();
            
            retrofit = new Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .addConverterFactory(GsonConverterFactory.create())
                    .client(client)
                    .build();
            
            apiInterface = retrofit.create(ApiInterface.class);
        }
        return apiInterface;
    }
}
''')
    
    # ApiResponse.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/network/ApiResponse.java", '''package com.farmconnect.network;

public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
    private String error;
    
    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public T getData() { return data; }
    public void setData(T data) { this.data = data; }
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
}
''')

def generate_utils():
    """Generate utility classes"""
    
    # SessionManager.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/utils/SessionManager.java", '''package com.farmconnect.utils;

import android.content.Context;
import android.content.SharedPreferences;
import com.farmconnect.models.User;
import com.google.gson.Gson;

public class SessionManager {
    private static final String PREF_NAME = "FarmConnectPref";
    private static final String KEY_IS_LOGGED_IN = "isLoggedIn";
    private static final String KEY_USER_DATA = "userData";
    private static final String KEY_TOKEN = "token";
    
    private SharedPreferences pref;
    private SharedPreferences.Editor editor;
    private Gson gson;
    
    public SessionManager(Context context) {
        pref = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        editor = pref.edit();
        gson = new Gson();
    }
    
    public void saveUser(User user) {
        String userJson = gson.toJson(user);
        editor.putBoolean(KEY_IS_LOGGED_IN, true);
        editor.putString(KEY_USER_DATA, userJson);
        if (user.getToken() != null) {
            editor.putString(KEY_TOKEN, user.getToken());
        }
        editor.apply();
    }
    
    public User getUser() {
        String userJson = pref.getString(KEY_USER_DATA, "");
        return gson.fromJson(userJson, User.class);
    }
    
    public String getUserName() {
        User user = getUser();
        return user != null ? user.getName() : "";
    }
    
    public String getUserEmail() {
        User user = getUser();
        return user != null ? user.getEmail() : "";
    }
    
    public String getUserRole() {
        User user = getUser();
        return user != null ? user.getRole() : "";
    }
    
    public String getToken() {
        return pref.getString(KEY_TOKEN, "");
    }
    
    public boolean isLoggedIn() {
        return pref.getBoolean(KEY_IS_LOGGED_IN, false);
    }
    
    public void logout() {
        editor.clear();
        editor.apply();
    }
}
''')
    
    # Constants.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/utils/Constants.java", '''package com.farmconnect.utils;

public class Constants {
    public static final String USSD_CODE = "*384*7321#";
    public static final String[] COMMODITIES = {"Maize", "Tomatoes", "Beans", "Groundnuts", "Rice", "Soybeans"};
    public static final String[] MARKETS = {"Lusaka", "Kabwe", "Ndola", "Livingstone", "Chipata", "Kitwe"};
}
''')

def generate_activities():
    """Generate activity classes"""
    
    # SplashActivity.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/activities/SplashActivity.java", '''package com.farmconnect.activities;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import androidx.appcompat.app.AppCompatActivity;
import com.farmconnect.utils.SessionManager;

public class SplashActivity extends AppCompatActivity {
    
    private SessionManager sessionManager;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);
        
        sessionManager = new SessionManager(this);
        
        new Handler().postDelayed(() -> {
            if (sessionManager.isLoggedIn()) {
                startActivity(new Intent(SplashActivity.this, MainActivity.class));
            } else {
                startActivity(new Intent(SplashActivity.this, LoginActivity.class));
            }
            finish();
        }, 2000);
    }
}
''')
    
    # LoginActivity.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/activities/LoginActivity.java", '''package com.farmconnect.activities;

import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.farmconnect.R;
import com.farmconnect.network.ApiClient;
import com.farmconnect.network.ApiInterface;
import com.farmconnect.network.ApiResponse;
import com.farmconnect.models.User;
import com.farmconnect.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import java.util.HashMap;
import java.util.Map;

public class LoginActivity extends AppCompatActivity {
    
    private EditText etUsername, etPassword;
    private Button btnLogin, btnRegister;
    private ProgressBar progressBar;
    private TextView tvError;
    private SessionManager sessionManager;
    private ApiInterface apiInterface;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        
        etUsername = findViewById(R.id.et_username);
        etPassword = findViewById(R.id.et_password);
        btnLogin = findViewById(R.id.btn_login);
        btnRegister = findViewById(R.id.btn_register);
        progressBar = findViewById(R.id.progress_bar);
        tvError = findViewById(R.id.tv_error);
        
        sessionManager = new SessionManager(this);
        apiInterface = ApiClient.getClient();
        
        btnLogin.setOnClickListener(v -> login());
        btnRegister.setOnClickListener(v -> 
            startActivity(new Intent(LoginActivity.this, RegisterActivity.class))
        );
    }
    
    private void login() {
        String username = etUsername.getText().toString().trim();
        String password = etPassword.getText().toString().trim();
        
        if (username.isEmpty() || password.isEmpty()) {
            tvError.setText("Please fill all fields");
            tvError.setVisibility(View.VISIBLE);
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        tvError.setVisibility(View.GONE);
        
        Map<String, String> credentials = new HashMap<>();
        credentials.put("username", username);
        credentials.put("password", password);
        
        apiInterface.login(credentials).enqueue(new Callback<ApiResponse<User>>() {
            @Override
            public void onResponse(Call<ApiResponse<User>> call, Response<ApiResponse<User>> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    User user = response.body().getData();
                    sessionManager.saveUser(user);
                    Toast.makeText(LoginActivity.this, "Welcome " + user.getName(), Toast.LENGTH_SHORT).show();
                    startActivity(new Intent(LoginActivity.this, MainActivity.class));
                    finish();
                } else {
                    tvError.setText("Invalid credentials");
                    tvError.setVisibility(View.VISIBLE);
                }
            }
            
            @Override
            public void onFailure(Call<ApiResponse<User>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                tvError.setText("Network error: " + t.getMessage());
                tvError.setVisibility(View.VISIBLE);
            }
        });
    }
}
''')
    
    # MainActivity.java
    write_file("FarmConnect/app/src/main/java/com/farmconnect/activities/MainActivity.java", '''package com.farmconnect.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import com.farmconnect.R;
import com.farmconnect.utils.SessionManager;

public class MainActivity extends AppCompatActivity implements View.OnClickListener {
    
    private CardView cardPrices, cardForecast, cardBuyers, cardProfile;
    private TextView tvWelcome;
    private SessionManager sessionManager;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        sessionManager = new SessionManager(this);
        
        cardPrices = findViewById(R.id.card_prices);
        cardForecast = findViewById(R.id.card_forecast);
        cardBuyers = findViewById(R.id.card_buyers);
        cardProfile = findViewById(R.id.card_profile);
        tvWelcome = findViewById(R.id.tv_welcome);
        
        cardPrices.setOnClickListener(this);
        cardForecast.setOnClickListener(this);
        cardBuyers.setOnClickListener(this);
        cardProfile.setOnClickListener(this);
        
        tvWelcome.setText("Welcome, " + sessionManager.getUserName());
    }
    
    @Override
    public void onClick(View v) {
        int id = v.getId();
        if (id == R.id.card_prices) {
            startActivity(new Intent(this, MarketPricesActivity.class));
        } else if (id == R.id.card_forecast) {
            startActivity(new Intent(this, PriceForecastActivity.class));
        } else if (id == R.id.card_buyers) {
            startActivity(new Intent(this, BuyersActivity.class));
        } else if (id == R.id.card_profile) {
            startActivity(new Intent(this, ProfileActivity.class));
        }
    }
}
''')
    
    # Placeholder for other activities
    for act in ["MarketPricesActivity", "PriceForecastActivity", "BuyersActivity", "ProfileActivity", "RegisterActivity"]:
        write_file(f"FarmConnect/app/src/main/java/com/farmconnect/activities/{act}.java", f'''package com.farmconnect.activities;

import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.farmconnect.R;

public class {act} extends AppCompatActivity {{
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_{act.toLowerCase().replace("activity", "")});
        
        TextView tvTitle = findViewById(R.id.tv_title);
        if (tvTitle != null) {{
            tvTitle.setText("{act.replace("Activity", "")}");
        }}
    }}
}}
''')

def generate_layouts():
    """Generate layout files"""
    
    # activity_splash.xml
    write_file("FarmConnect/app/src/main/res/layout/activity_splash.xml", '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:gravity="center"
    android:background="#2E8B57"
    android:orientation="vertical">
    
    <ImageView
        android:layout_width="120dp"
        android:layout_height="120dp"
        android:src="@drawable/ic_farmconnect_logo"
        android:layout_marginBottom="24dp"/>
    
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="FarmConnect Zambia"
        android:textSize="28sp"
        android:textStyle="bold"
        android:textColor="@android:color/white"/>
    
    <ProgressBar
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="32dp"
        android:indeterminateTint="@android:color/white"/>
        
</LinearLayout>
''')
    
    # activity_login.xml
    write_file("FarmConnect/app/src/main/res/layout/activity_login.xml", '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="24dp"
    android:gravity="center"
    android:background="@android:color/white">
    
    <ImageView
        android:layout_width="100dp"
        android:layout_height="100dp"
        android:src="@drawable/ic_farmconnect_logo"
        android:layout_marginBottom="24dp"/>
    
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="FarmConnect"
        android:textSize="24sp"
        android:textStyle="bold"
        android:textColor="#2E8B57"
        android:layout_marginBottom="32dp"/>
    
    <EditText
        android:id="@+id/et_username"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:hint="Username"
        android:padding="16dp"
        android:background="@drawable/edittext_border"/>
    
    <EditText
        android:id="@+id/et_password"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:hint="Password"
        android:inputType="textPassword"
        android:padding="16dp"
        android:layout_marginTop="16dp"
        android:background="@drawable/edittext_border"/>
    
    <TextView
        android:id="@+id/tv_error"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textColor="#FF0000"
        android:visibility="gone"
        android:layout_marginTop="16dp"/>
    
    <Button
        android:id="@+id/btn_login"
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:text="LOGIN"
        android:backgroundTint="#2E8B57"
        android:layout_marginTop="24dp"/>
    
    <ProgressBar
        android:id="@+id/progress_bar"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:layout_marginTop="16dp"
        android:visibility="gone"/>
    
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Don't have an account?"
        android:layout_marginTop="24dp"/>
    
    <Button
        android:id="@+id/btn_register"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="REGISTER"
        android:background="@android:color/transparent"
        android:textColor="#2E8B57"
        android:textStyle="bold"/>
        
</LinearLayout>
''')
    
    # activity_main.xml
    write_file("FarmConnect/app/src/main/res/layout/activity_main.xml", '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp"
    android:background="@android:color/white">
    
    <TextView
        android:id="@+id/tv_welcome"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Welcome!"
        android:textSize="24sp"
        android:textStyle="bold"
        android:textColor="#2E8B57"
        android:layout_marginBottom="24dp"/>
    
    <GridLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:columnCount="2"
        android:rowCount="2">
        
        <androidx.cardview.widget.CardView
            android:id="@+id/card_prices"
            android:layout_width="0dp"
            android:layout_height="150dp"
            android:layout_margin="8dp"
            android:layout_columnWeight="1"
            app:cardCornerRadius="12dp"
            app:cardElevation="4dp">
            
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:orientation="vertical"
                android:gravity="center"
                android:background="@android:color/white">
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="📊"
                    android:textSize="48sp"/>
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Market Prices"
                    android:textSize="16sp"
                    android:textStyle="bold"
                    android:layout_marginTop="8dp"/>
                    
            </LinearLayout>
        </androidx.cardview.widget.CardView>
        
        <androidx.cardview.widget.CardView
            android:id="@+id/card_forecast"
            android:layout_width="0dp"
            android:layout_height="150dp"
            android:layout_margin="8dp"
            android:layout_columnWeight="1"
            app:cardCornerRadius="12dp"
            app:cardElevation="4dp">
            
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:orientation="vertical"
                android:gravity="center"
                android:background="@android:color/white">
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="📈"
                    android:textSize="48sp"/>
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Price Forecast"
                    android:textSize="16sp"
                    android:textStyle="bold"
                    android:layout_marginTop="8dp"/>
                    
            </LinearLayout>
        </androidx.cardview.widget.CardView>
        
        <androidx.cardview.widget.CardView
            android:id="@+id/card_buyers"
            android:layout_width="0dp"
            android:layout_height="150dp"
            android:layout_margin="8dp"
            android:layout_columnWeight="1"
            app:cardCornerRadius="12dp"
            app:cardElevation="4dp">
            
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:orientation="vertical"
                android:gravity="center"
                android:background="@android:color/white">
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="🤝"
                    android:textSize="48sp"/>
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="Find Buyers"
                    android:textSize="16sp"
                    android:textStyle="bold"
                    android:layout_marginTop="8dp"/>
                    
            </LinearLayout>
        </androidx.cardview.widget.CardView>
        
        <androidx.cardview.widget.CardView
            android:id="@+id/card_profile"
            android:layout_width="0dp"
            android:layout_height="150dp"
            android:layout_margin="8dp"
            android:layout_columnWeight="1"
            app:cardCornerRadius="12dp"
            app:cardElevation="4dp">
            
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:orientation="vertical"
                android:gravity="center"
                android:background="@android:color/white">
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="👤"
                    android:textSize="48sp"/>
                
                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:text="My Profile"
                    android:textSize="16sp"
                    android:textStyle="bold"
                    android:layout_marginTop="8dp"/>
                    
            </LinearLayout>
        </androidx.cardview.widget.CardView>
        
    </GridLayout>
    
    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="📱 USSD: *384*7321#"
        android:gravity="center"
        android:padding="12dp"
        android:background="#F5F5F5"
        android:layout_marginTop="24dp"
        android:textStyle="bold"/>
        
</LinearLayout>
''')

def generate_resources():
    """Generate resource files"""
    
    # colors.xml
    write_file("FarmConnect/app/src/main/res/values/colors.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary_green">#2E8B57</color>
    <color name="primary_dark_green">#1f6b43</color>
    <color name="accent_orange">#FFA500</color>
    <color name="white">#FFFFFF</color>
    <color name="black">#000000</color>
</resources>
''')
    
    # strings.xml
    write_file("FarmConnect/app/src/main/res/values/strings.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">FarmConnect Zambia</string>
    <string name="ussd_code">*384*7321#</string>
</resources>
''')
    
    # themes.xml
    write_file("FarmConnect/app/src/main/res/values/themes.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.FarmConnect" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">@color/primary_green</item>
        <item name="colorPrimaryVariant">@color/primary_dark_green</item>
        <item name="colorOnPrimary">@color/white</item>
    </style>
</resources>
''')
    
    # edittext_border.xml (drawable)
    write_file("FarmConnect/app/src/main/res/drawable/edittext_border.xml", '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <stroke android:width="1dp" android:color="#CCCCCC"/>
    <corners android:radius="8dp"/>
</shape>
''')
    
    # Placeholder for logo
    write_file("FarmConnect/app/src/main/res/drawable/ic_farmconnect_logo.xml", '''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#2E8B57"/>
    <size android:width="120dp" android:height="120dp"/>
</shape>
''')

def main():
    """Main function to generate all files"""
    print("=" * 50)
    print("🌾 FarmConnect Android Project Generator")
    print("=" * 50)
    
    # Create all directories
    create_directories()
    
    # Generate all files
    generate_gradle_files()
    generate_manifest()
    generate_models()
    generate_network()
    generate_utils()
    generate_activities()
    generate_layouts()
    generate_resources()
    
    print("=" * 50)
    print("✅ SUCCESS! All files generated!")
    print("=" * 50)
    print("\n📁 Project location: ./FarmConnect/")
    print("\n🚀 Next steps:")
    print("1. Open Android Studio")
    print("2. Select 'Open an Existing Project'")
    print("3. Navigate to and select the 'FarmConnect' folder")
    print("4. Wait for Gradle sync to complete")
    print("5. Run the app on an emulator or device")
    print("\n🔑 Demo credentials:")
    print("   Username: farmer1")
    print("   Password: farmer123")
    print("=" * 50)

if __name__ == "__main__":
    main()