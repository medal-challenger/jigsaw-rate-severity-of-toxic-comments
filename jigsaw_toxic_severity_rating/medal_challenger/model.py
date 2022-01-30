import torch
import torch.nn as nn
from transformers import AutoModel
from torch.optim import lr_scheduler
from medal_challenger.configs import SCHEDULER_LIST
from transformers import AutoConfig

class AttentionBlock(nn.Module):
    def __init__(self, in_features, middle_features, out_features):
        super().__init__()
        self.in_features = in_features
        self.middle_features = middle_features
        self.out_features = out_features
        self.W = nn.Linear(in_features, middle_features)
        self.V = nn.Linear(middle_features, out_features)

    def forward(self, features):
        att = torch.tanh(self.W(features))
        score = self.V(att)
        attention_weights = torch.softmax(score, dim=1)
        context_vector = attention_weights * features
        context_vector = torch.sum(context_vector, dim=1)
        return context_vector
    
class JigsawModel(nn.Module):
    
    def __init__(self, model_name, num_classes, drop_p):
        super().__init__()
        self.model = AutoModel.from_pretrained(model_name)
        self.drop = nn.Dropout(drop_p)
        self.first_layer = nn.Linear(
            1024 
            if 'large' in model_name
            else 768,
            256)
        
        
        self.attention = nn.Sequential(
           nn.LayerNorm(768),
            nn.Dropout(drop_p),
           AttentionBlock(768, 768, 1)
        )
        self.fc = nn.Sequential(
            self.first_layer,
            nn.LayerNorm(256),
            nn.Dropout(drop_p),
            nn.ReLU(),
            nn.Linear(256, num_classes),
        )
        self.model_name = model_name
        
    def forward(self, ids, mask):        
        out = self.model(
            input_ids=ids,
            attention_mask=mask,
            output_hidden_states=False
        )
        out = self.attention(out[0])
        outputs = self.fc(out)
        return outputs

'''
    def __init__(self, model_name, num_classes, drop_p):
        super().__init__()

        config = AutoConfig.from_pretrained(model_name)
        config.update({"output_hidden_states": True,
                       "hidden_dropout_prob": drop_p,
                       "layer_norm_eps": 1e-7})

        self.roberta = AutoModel.from_pretrained(model_name, config=config)

        self.attention1 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )
        self.attention2 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )
        self.attention4 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )
        self.attention8 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )
        self.attention16 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )
        self.attention20 = nn.Sequential(
            nn.Linear(768, 256),
            nn.Tanh(),
            nn.Linear(256, 1),
            nn.Softmax(dim=1)
        )

        self.attention_sm = nn.Sequential(
            nn.Linear(768, 6),
            nn.Tanh(),
            nn.Linear(6, 1),
            nn.Softmax(dim=1)
        )

        self.regressor = nn.Sequential(
            nn.Linear(768, num_classes)
        )

    def forward(self, input_ids, attention_mask):
        roberta_output = self.roberta(input_ids=input_ids,
                                      attention_mask=attention_mask)

        # There are a total of 13 layers of hidden states.
        # 1 for the embedding layer, and 12 for the 12 Roberta layers.
        # We take the hidden states from the last Roberta layer.
        last_layer_hidden_states = roberta_output.hidden_states[-1]
        weights_1 = self.attention1(last_layer_hidden_states)
        context_vector_1 = torch.sum(
            weights_1 * last_layer_hidden_states, dim=1)

        last2_layer_hidden_states = roberta_output.hidden_states[-2]
        weights_2 = self.attention2(last2_layer_hidden_states)
        context_vector_2 = torch.sum(
            weights_2 * last2_layer_hidden_states, dim=1)

        last4_layer_hidden_states = roberta_output.hidden_states[-4]
        weights_4 = self.attention4(last4_layer_hidden_states)
        context_vector_4 = torch.sum(
            weights_4 * last4_layer_hidden_states, dim=1)

        last8_layer_hidden_states = roberta_output.hidden_states[-8]
        weights_8 = self.attention8(last8_layer_hidden_states)
        context_vector_8 = torch.sum(
            weights_8 * last8_layer_hidden_states, dim=1)

        last16_layer_hidden_states = roberta_output.hidden_states[-11]
        weights_16 = self.attention16(last16_layer_hidden_states)
        context_vector_16 = torch.sum(
            weights_16 * last16_layer_hidden_states, dim=1)

        last20_layer_hidden_states = roberta_output.hidden_states[-13]
        weights_20 = self.attention20(last20_layer_hidden_states)
        context_vector_20 = torch.sum(
            weights_20 * last20_layer_hidden_states, dim=1)

        con_context_vectors = torch.stack(
            [context_vector_1, context_vector_2, context_vector_4, context_vector_8, context_vector_16, context_vector_20], dim=1)

#         print(context_vector_1.shape)
        # con_context_vectors = torch.stack([context_vector_1, context_vector_2, context_vector_4, context_vector_8], dim=1)
#         print(con_context_vectors.shape)
        layer_weights = self.attention_sm(con_context_vectors)
#         print(layer_weights.shape)
        final_context_vector = torch.sum(
            layer_weights * con_context_vectors, dim=1)

#         print(final_context_vector.shape)
        ans = self.regressor(final_context_vector)
#         print(ans.shape)

        # Now we reduce the context vector to the prediction score.
        return ans
'''

def fetch_scheduler(optimizer, cfg):
    '''
        Config에 맞는 Solver Scheduler를 반환합니다.
    '''
    if SCHEDULER_LIST[cfg.model_param.scheduler] == 'CosineAnnealingLR':
        scheduler = lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=cfg.train_param.T_max, 
            eta_min=float(cfg.train_param.min_lr)
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'CosineAnnealingWarmRestarts':
        scheduler = lr_scheduler.CosineAnnealingWarmRestarts(
            optimizer,
            T_0=cfg.train_param.T_0, 
            eta_min=float(cfg.train_param.min_lr)
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'LambdaLR':
        scheduler = lr_scheduler.LambdaLR(
            optimizer,
            lr_lambda=lambda epoch: cfg.train_param.reduce_ratio ** epoch
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'MultiplicativeLR':
        scheduler = lr_scheduler.MultiplicativeLR(
            optimizer,
            lr_lambda=lambda epoch: cfg.train_param.reduce_ratio ** epoch
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'StepLR':
        scheduler = lr_scheduler.StepLR(
            optimizer,
            step_size=cfg.train_param.step_size, gamma=cfg.train_param.gamma
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'MultiStepLR':
        scheduler = lr_scheduler.MultiStepLR(
            optimizer,
             milestones=cfg.train_param.milestones, gamma=cfg.train_param.gamma
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'ExponentialLR':
        scheduler = lr_scheduler.ExponentialLR(
            optimizer,
            gamma=cfg.train_param.gamma
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'ReduceLROnPlateau':
        scheduler = lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min', min_lr=cfg.train_param.min_lr
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'CyclicLR':
        scheduler = lr_scheduler.CyclicLR(
            optimizer,
            base_lr=float(cfg.train_param.base_lr), 
            step_size_up=cfg.train_param.step_size_up, 
            max_lr=float(cfg.train_param.lr), 
            gamma=cfg.train_param.gamma, 
            mode='exp_range'
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'OneCycleLR':
        scheduler = lr_scheduler.OneCycleLR(
            optimizer,
            max_lr=cfg.train_param.max_lr, 
            steps_per_epoch=cfg.train_param.steps_per_epoch, 
            epochs=cfg.train_param.epochs,
            anneal_strategy='linear'
        )
    elif SCHEDULER_LIST[cfg.model_param.scheduler] == 'None':
        return None
        
    return scheduler