#include <SFML/Graphics.hpp>
#include <stdio.h>
#include <iostream>
#include "socket_server.cpp" 
#include "game_state_sender.cpp"

using namespace sf;
using namespace std;

#define healthH 25
#define healthW 200

#define height 305.f
#define hamza2k21 60.f
#define screenWidth 1400.f
#define screenHeight 800.f
#define attackState "ATTACK"
#define idleState "IDLE"
#define fmoveState "FORWARD"
#define bmoveState "BACK"
#define jumpState "JUMP"
#define shieldState "SHIELD"

class Character {
protected:
    bool jumping = false;
    bool jumpStarted = false;
    float jumpDuration = 0.5f;
    float jumpTimeElapsed = 0;
    float jumpDistance = 150.f;
    float moveDistance = 70.f;
    float moveDuration = 0.25f;
    float moveTimeElapsed = 0;
    float shieldDuration = 0.5f;
    float shieldTimeElapsed = 0;
    float attackDuration = 0.35f;
    float attackTimeElapsed = 0;

    int health = 100;
    string state = idleState;
    bool movingLeft = false;
    bool movingRight = false;
    bool shielding = false;
    bool attacking = false;
    bool attackdone = false;

public:
    int framecycle;
    int frameWidth;
    int frameHeight;

    virtual ~Character() {}

    virtual void draw(sf::RenderWindow& window) = 0;
    virtual Vector2f getPosition() = 0;
    virtual void move(const sf::Vector2f& velocity) = 0;

    bool isJumping() {
        return jumping || jumpStarted;
    }

    bool isMoving() {
        return movingLeft || movingRight;
    }

    bool isShielding() {
        return shielding;
    }

    bool isAttacking() {
        return attacking;
    }

    string getState() {
        return state;
    }

    int getHealth() {
        return health;
    }

    void takeDamage(int damage) {
        health -= damage;
        if (health < 0) health = 0;
    }

    void handleInput(String action, float dt) {
        if (action == "left") {
            if (isMoving()) moveTimeElapsed = 0; // Reset move time to allow immediate direction change
            movingLeft = true;
            movingRight = false;
            shielding = false;
            state = bmoveState;
            handleMove(dt);
        }
        else if (action == "right") {
            if (isMoving()) moveTimeElapsed = 0;
            movingRight = true;
            movingLeft = false;
            shielding = false;
            state = fmoveState;
            handleMove(dt);
        }
        else if (action == "jump") {
            state = jumpState;
            shielding = false;
            handleJump(dt);
        }
    }

    //once jump is initiated, use time to simulate gravity and bring Player back down
    void handleJump(float dt) {
        if (jumping) {
            jumpTimeElapsed += dt;
            if (getPosition().y < (screenHeight - height)) {
                move(Vector2f(0, jumpDistance * dt / (jumpDuration - jumpTimeElapsed)));
            }
            else {
                move(Vector2f(0, screenHeight - height - getPosition().y));
                jumping = false;
                state = idleState;
                jumpTimeElapsed = 0;
            }
        }
        else {
            jumpTimeElapsed += dt;
            if (getPosition().y > (screenHeight - height - jumpDistance)) {
                move(Vector2f(0, -jumpDistance * dt / (jumpDuration - jumpTimeElapsed)));
                jumpStarted = true;
            }
            else {
                if (jumpTimeElapsed >= jumpDuration) {
                    jumping = true;
                    jumpStarted = false;
                    jumpTimeElapsed = 0;
                }
            }
        }
    }

    virtual void handleMove(float dt) {
        if (movingLeft) {
            move(Vector2f(-moveDistance * dt / moveDuration, 0));
            moveTimeElapsed += dt;
            if (moveTimeElapsed >= moveDuration) {
                movingLeft = false;
                moveTimeElapsed = 0;
                state = idleState;
            }
        }
        else if (movingRight) {
            move(Vector2f(moveDistance * dt / moveDuration, 0));
            moveTimeElapsed += dt;
            if (moveTimeElapsed >= moveDuration) {
                movingRight = false;
                moveTimeElapsed = 0;
                state = idleState;
            }
        }
    }

    virtual void handleShield(float dt) {
        state = shieldState;
        shielding = true;
        shieldTimeElapsed += dt;
        if (shieldTimeElapsed >= shieldDuration) {
            shieldTimeElapsed = 0;
            state = idleState;
            shielding = false;
        }
    }

    virtual void performAttack(Character& target, float dt) {
        shielding = false;
        attacking = true;
        state = attackState;
        attackTimeElapsed += dt;
        Vector2f tPos = target.getPosition();
        Vector2f myPos = getPosition();

        if (target.getState() != shieldState) {
            if (abs(myPos.x - tPos.x) < 200.f && abs(myPos.y - tPos.y) < 60.f
                && attackTimeElapsed > attackDuration / 2 && !attackdone) {
                attackdone = true;
                target.takeDamage(10);
                cout << "Hit registered! Target health: " << target.getHealth() << endl;
            }
        }

        if (attackTimeElapsed >= attackDuration) {
            attackTimeElapsed = 0;
            state = idleState;
            attacking = false;
            attackdone = false;
        }
    }
};

class Player : public Character {
public:
    Sprite PlayerSprite;
    Texture charTexture;
    Texture walkTexture;
    Texture attack1Texture;
    Texture attack2Texture;
    Texture attack3Texture;
    int spriteSpeed = 100;
    int attackCount = 0;
    int kuchtouhai = 200;
    int currentFrame = 0;

    Player() {
        framecycle = 8;
        frameWidth = 64;
        frameHeight = 112;
        charTexture.loadFromFile("Assets/Martial Hero/Sprites/Idle.png");
        walkTexture.loadFromFile("Assets/Martial Hero/Sprites/Run.png");
        attack1Texture.loadFromFile("Assets/Martial Hero/Sprites/Attack1.png");
        attack2Texture.loadFromFile("Assets/Martial Hero/Sprites/Attack2.png");
        //attack3Texture.loadFromFile("Assets/Martial Hero/Sprites/idle.png");
        PlayerSprite.setTexture(charTexture);
        PlayerSprite.setPosition(200.f, screenHeight - height);
        PlayerSprite.setTextureRect(IntRect(0, 0, 64, 64));
        PlayerSprite.setScale(2.0f, 2.0f);
    }

    void draw(sf::RenderWindow& window) override {
        window.draw(PlayerSprite);
    }

    Vector2f getPosition() override {
        return PlayerSprite.getPosition();
    }

    void move(const sf::Vector2f& velocity) override {
        PlayerSprite.move(velocity);
        // Clamp position to screen bounds
        sf::Vector2f pos = PlayerSprite.getPosition();
        if (pos.x < 0.f) pos.x = 0.f;
        if (pos.x > screenWidth) pos.x = screenWidth;
        if (pos.y < 0.f) pos.y = 0.f;
        if (pos.y > screenHeight - height) pos.y = screenHeight - height;
        PlayerSprite.setPosition(pos);
    }

    void handleMove(float dt) override {
        frameWidth = 84;
        if (movingLeft) {
            PlayerSprite.setScale(-2.f, 2.f);
            PlayerSprite.setOrigin(100.f, 0.f);

            if (!attacking) {
                PlayerSprite.setTexture(walkTexture);
                framecycle = 8;
                spriteSpeed = 60; // ms per frame for running
            }
        }
        else if (movingRight) {
            PlayerSprite.setScale(2.f, 2.f);
            PlayerSprite.setOrigin(0.f, 0.f);

            if (!attacking) {
                PlayerSprite.setTexture(walkTexture);
                framecycle = 8;
                spriteSpeed = 60; // ms per frame for running
            }
        }

        Character::handleMove(dt);

        if (state == idleState) {
            PlayerSprite.setTexture(charTexture);
            framecycle = 8;
            spriteSpeed = 100; // ms per frame for idle
        }
    }

    void performAttack(Character& target, float dt) override {
        if (!attacking) {
            frameWidth = 140;
            //kuchtouhai = 106;
            currentFrame = 0; // Reset to first frame of attack animation
            if (attackCount == 0) {
                framecycle = 6;
                spriteSpeed = 70; // ms per frame for attack 1
                PlayerSprite.setTexture(attack1Texture);
                attackCount++;

            }
            else if (attackCount == 1) {
                framecycle = 6;
                spriteSpeed = 70; // ms per frame for attack 2
                PlayerSprite.setTexture(attack2Texture);
                attackCount = 0;
            }
            //else if (attackCount == 2) {
            //    framecycle = 6;
            //    spriteSpeed = 100; // ms per frame for attack 3
            //    PlayerSprite.setTexture(attack3Texture);
            //    attackCount = 0;
            //}
        }


        Character::performAttack(target, dt);

        if (state == idleState) {
            PlayerSprite.setTexture(charTexture);
            framecycle = 8;
            frameWidth = 97;
            currentFrame = 0; // Reset to first frame of idle animation
            //kuchtouhai = 96;
            spriteSpeed = 100; // ms per frame for idle
        }

    }


};

class Enemy : public Character {
    RectangleShape shape;
public:
    Sprite EnemySprite;
    Texture EnemyIdleTexture;
    Texture EnemyRunTexture;
    Texture Enemyattack1Texture;
    Texture Enemyattack2Texture;
    Texture Enemyattack3Texture;
    int EnemyspriteSpeed = 100;
    int EnemyattackCount = 0;
    int kuchtouhai = 250;
    int EnemycurrentFrame = 0;
    Enemy() {
        framecycle = 8;
        frameWidth = 77;
        frameHeight = 110;
        //shape.setSize(sf::Vector2f(hamza2k21, height)); 
        //shape.setFillColor(sf::Color::Red);
        //shape.setPosition(1000.f, screenHeight - height);
        EnemyIdleTexture.loadFromFile("Assets/EVil Wizard 2/Sprites/idle.png");
        EnemyRunTexture.loadFromFile("Assets/EVil Wizard 2/Sprites/Run.png");
        Enemyattack1Texture.loadFromFile("Assets/EVil Wizard 2/Sprites/Attack1.png");
        Enemyattack2Texture.loadFromFile("Assets/EVil Wizard 2/Sprites/Attack2.png");
        EnemySprite.setTexture(EnemyIdleTexture);
        EnemySprite.setPosition(1000.f, screenHeight - height);
        EnemySprite.setTextureRect(IntRect(0, 0, 64, 64));
        EnemySprite.setScale(2.0f, 2.0f);
    }

    void draw(sf::RenderWindow& window) override {
        window.draw(EnemySprite);
        //window.draw(shape); 
    }

    Vector2f getPosition() override {
        return EnemySprite.getPosition();
        //return shape.getPosition(); 
    }

    void move(const sf::Vector2f& velocity) override {
        EnemySprite.move(velocity);
        // Clamp position to screen bounds
        sf::Vector2f pos = EnemySprite.getPosition();
        if (pos.x < 0.f) pos.x = 0.f;
        if (pos.x > screenWidth) pos.x = screenWidth;
        if (pos.y < 0.f) pos.y = 0.f;
        if (pos.y > screenHeight - height) pos.y = screenHeight - height;
        EnemySprite.setPosition(pos);
        //shape.move(velocity); 
    }


    void handleMove(float dt) override {
        frameWidth = 130;
        frameHeight = 120;
        if (movingLeft && getPosition().x > 0) {
            EnemySprite.setScale(2.f, 2.f);
            EnemySprite.setOrigin(0.f, 0.f);

            if (!attacking) {
                EnemySprite.setTexture(EnemyRunTexture);
                framecycle = 8;
                EnemyspriteSpeed = 60; // ms per frame for running
            }
        }
        else if (movingRight && getPosition().x < 1400) {
            EnemySprite.setScale(-2.f, 2.f);
            EnemySprite.setOrigin(100.f, 0.f);

            if (!attacking) {
                EnemySprite.setTexture(EnemyRunTexture);
                framecycle = 8;
                EnemyspriteSpeed = 60; // ms per frame for running
            }
        }

        Character::handleMove(dt);

        if (state == idleState) {
            frameWidth = 77;
            frameHeight = 110;
            EnemySprite.setTexture(EnemyIdleTexture);
            framecycle = 8;
            EnemyspriteSpeed = 100; // ms per frame for idle
        }
    }

    void performAttack(Character& target, float dt) override {
        if (!attacking) {
            frameWidth = 200;
            frameHeight = 200;
            //kuchtouhai = 106;
            EnemycurrentFrame = 0; // Reset to first frame of attack animation
            if (EnemyattackCount == 0) {
                framecycle = 8;
                EnemyspriteSpeed = 100; // ms per frame for attack 1
                EnemySprite.setTexture(Enemyattack1Texture);
                EnemyattackCount++;

            }
            else if (EnemyattackCount == 1) {
                framecycle = 8;
                EnemyspriteSpeed = 100; // ms per frame for attack 2
                EnemySprite.setTexture(Enemyattack2Texture);
                EnemyattackCount = 0;
            }
            //else if (EnemyattackCount == 2) {
            //    framecycle = 6;
            //    EnemyspriteSpeed = 100; // ms per frame for attack 3
            //    EnemySprite.setTexture(Enemyattack3Texture);
            //    EnemyattackCount = 0;
            //}
        }


        Character::performAttack(target, dt);

        if (state == idleState) {
            EnemySprite.setTexture(EnemyIdleTexture);
            framecycle = 8;
            frameWidth = 77;
            frameHeight = 110;
            EnemycurrentFrame = 0; // Reset to first frame of idle animation
            //kuchtouhai = 96;
            EnemyspriteSpeed = 100; // ms per frame for idle
        }

    }
};

int main() {
    sf::RenderWindow window(sf::VideoMode(screenWidth, screenHeight), "Fighting Game");


    sf::RectangleShape box1(sf::Vector2f(healthW, healthH));
    
    box1.setFillColor(sf::Color(0, 100, 0));
    box1.setPosition(100, 55);
    box1.setOutlineThickness(5);
    box1.setOutlineColor(sf::Color::Black);

    sf::RectangleShape box2(sf::Vector2f(healthW, healthH));
    box2.setFillColor(sf::Color(196, 30, 58));
    box2.setPosition(1100, 55);
    box2.setOutlineThickness(5);
    box2.setOutlineColor(sf::Color::Black);

	Texture GameOverTexture;
	Sprite GameOverSprite;
	GameOverTexture.loadFromFile("Assets/Background/GameOver.png");
    GameOverSprite.setTexture(GameOverTexture);
	GameOverSprite.setPosition(400.f, 200.f);

    Texture backgroundTexture;
    Sprite backgroundSprite;
    backgroundTexture.loadFromFile("Assets/Background/Background2.png");
    backgroundSprite.setTexture(backgroundTexture);
    backgroundSprite.setPosition(0.f, 0.f);

    Player c1;
    Enemy e1;
    Clock clock;
    Clock animationClock;
    float dt;

    auto onGesture = [&c1, &dt, &e1](int player, const string& gesture) {
        if (player == 1) {
            if (gesture == "FORWARD") c1.handleInput("right", dt);
            else if (gesture == "BACKWARD") c1.handleInput("left", dt);
            else if (gesture == "JUMP" && !c1.isJumping()) c1.handleInput("jump", dt);
            else if (gesture == "ATTACK" && !c1.isJumping()) c1.performAttack(e1, dt);
            else if (gesture == "SHIELD") c1.handleShield(dt);
        }
        if (player == 0) {
            if (gesture == "FORWARD") e1.handleInput("right", dt);
            else if (gesture == "BACKWARD") e1.handleInput("left", dt);
            else if (gesture == "JUMP" && !e1.isJumping()) e1.handleInput("jump", dt);
            else if (gesture == "ATTACK" && !e1.isJumping()) e1.performAttack(c1, dt);
            else if (gesture == "SHIELD") e1.handleShield(dt);
        }
        };

    GestureReceiver recv(5005, onGesture);
    GameStateSender stateTx("127.0.0.1", 5006);

    while (window.isOpen()) {
        Event event;
        dt = clock.restart().asSeconds();
        recv.poll();

        stateTx.send(
            { c1.getPosition().x, c1.getPosition().y, c1.getState(), c1.getHealth() },
            { e1.getPosition().x, e1.getPosition().y, "IDLE", e1.getHealth() }
        );

        if (animationClock.getElapsedTime().asMilliseconds() > c1.spriteSpeed) { // Change frame every 100ms
            c1.currentFrame = (c1.currentFrame + 1) % c1.framecycle; // Cycle through 7 frames
            c1.PlayerSprite.setTextureRect(IntRect(c1.currentFrame * c1.kuchtouhai, 0, c1.frameWidth, c1.frameHeight));

            e1.EnemycurrentFrame = (e1.EnemycurrentFrame + 1) % e1.framecycle; // Cycle through n frames
            e1.EnemySprite.setTextureRect(IntRect(e1.EnemycurrentFrame * e1.kuchtouhai, 0, e1.frameWidth, e1.frameHeight));
            animationClock.restart();
        }

        //if (animationClock.getElapsedTime().asMilliseconds() > e1.EnemyspriteSpeed) { // Change frame every n ms
        //    e1.EnemycurrentFrame = (e1.EnemycurrentFrame + 1) % e1.framecycle; // Cycle through n frames
        //    e1.EnemySprite.setTextureRect(IntRect(e1.EnemycurrentFrame * e1.kuchtouhai, 0, e1.frameWidth, e1.frameHeight));
        //    animationClock.restart();
        //}


        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) window.close();
            if (event.type == sf::Event::KeyPressed) {
                if (event.key.code == sf::Keyboard::Left) c1.handleInput("left", dt);
                else if (event.key.code == sf::Keyboard::Right) c1.handleInput("right", dt);
                else if (event.key.code == sf::Keyboard::Up && !c1.isJumping()) c1.handleInput("jump", dt);
                else if (event.key.code == sf::Keyboard::Space && !c1.isJumping()) c1.performAttack(e1, dt);
                else if (event.key.code == sf::Keyboard::Down) c1.handleShield(dt);
            }
        }

        if (c1.isJumping()) c1.handleJump(dt);
        if (c1.isMoving()) c1.handleMove(dt);
        if (c1.isShielding()) c1.handleShield(dt);
        if (c1.isAttacking()) c1.performAttack(e1, dt);

        if (e1.isJumping()) e1.handleJump(dt);
        if (e1.isMoving()) e1.handleMove(dt);
        if (e1.isShielding()) e1.handleShield(dt);
        if (e1.isAttacking()) e1.performAttack(c1, dt);

        box1.setSize(Vector2f(healthW * (c1.getHealth() / 100.f), healthH));
        box2.setSize(Vector2f(healthW * (e1.getHealth() / 100.f), healthH));

		if (e1.getHealth() <= 0 || c1.getHealth() <= 0) {
			GameOverSprite.setPosition(475.f, 300.f);
			GameOverSprite.setScale(0.25f, 0.25f);
			window.clear(sf::Color::Black);
			window.draw(GameOverSprite);
			window.display();
			continue;
		}

        window.clear(sf::Color::Black);
        window.draw(backgroundSprite);
        c1.draw(window);
        e1.draw(window);
        window.draw(box1);
        window.draw(box2);
        window.display();
    }
    return 0;
}